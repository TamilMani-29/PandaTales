"""Service layer for user registration and login."""

import asyncio
import smtplib
from email.message import EmailMessage

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BadRequestException, ConflictException, UnauthorizedException
from app.common.logging import get_logger
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import AuthResponse, AuthUserResponse, LoginRequest, RegisterRequest


logger = get_logger(__name__)


class AuthService:
    """Business logic for auth operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(db)

    async def register(self, payload: RegisterRequest) -> AuthResponse:
        """Register a new user and return JWT."""
        email = payload.email.strip().lower()
        existing = await self.repository.get_by_email(email, include_inactive=True)
        if existing:
            raise ConflictException(message="Email is already registered", error_code="EMAIL_EXISTS")

        referrer: User | None = None
        referral_code = (payload.referral_code or "").strip().upper()
        if referral_code:
            referrer = await self.repository.get_by_referral_code(referral_code)
            if not referrer:
                raise BadRequestException(message="Invalid referral code", error_code="INVALID_REFERRAL_CODE")
            if referrer.email.strip().lower() == email:
                raise BadRequestException(message="You cannot use your own referral code", error_code="SELF_REFERRAL")

        full_name = payload.full_name.strip()
        if not full_name:
            raise BadRequestException(message="Full name is required", error_code="INVALID_FULL_NAME")

        name_parts = [part for part in full_name.split(" ") if part]
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "-"
        normalized_phone = payload.phone

        user = await self.repository.create_from_signup(
            email=email,
            password_hash=get_password_hash(payload.password),
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            phone=normalized_phone,
        )

        if referrer is not None:
            referrer.referral_count = int(referrer.referral_count or 0) + 1
            updated_count = int(referrer.referral_count)
            await self.db.commit()

            if updated_count == 5:
                try:
                    await self._send_referral_reward_email(referrer)
                except Exception as exc:
                    logger.warning(
                        "referral_reward_email_failed",
                        user_id=str(referrer.id),
                        email=referrer.email,
                        error=str(exc),
                    )

        token = create_access_token(user.id)
        return AuthResponse(access_token=token, user=self._to_user_response(user))

    async def login(self, payload: LoginRequest) -> AuthResponse:
        """Authenticate user and return JWT."""
        user = await self.repository.get_by_email(payload.email.strip().lower(), include_inactive=True)
        if not user:
            raise UnauthorizedException(
                message="User does not exist. Please sign up first.",
                error_code="USER_NOT_FOUND",
            )
        if not user.is_active:
            raise UnauthorizedException(
                message="User account is inactive.",
                error_code="USER_INACTIVE",
            )

        if not verify_password(payload.password, user.password_hash):
            raise UnauthorizedException(
                message="Invalid password.",
                error_code="INVALID_PASSWORD",
            )

        await self.repository.update_last_login(user.id)
        token = create_access_token(user.id)
        return AuthResponse(access_token=token, user=self._to_user_response(user))

    def build_me_response(self, user: User) -> AuthUserResponse:
        """Build profile response for current user."""
        return self._to_user_response(user)

    def _to_user_response(self, user: User) -> AuthUserResponse:
        display_name = user.full_name or f"{user.first_name} {user.last_name}".strip()
        return AuthUserResponse(
            id=str(user.id),
            email=user.email,
            full_name=display_name,
            phone=user.phone,
            referral_code=user.referral_code,
            referral_count=user.referral_count,
        )

    async def _send_referral_reward_email(self, user: User) -> None:
        if not settings.SMTP_HOST or not settings.SMTP_PORT:
            return
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            return

        name = user.full_name or user.first_name or "there"
        message = EmailMessage()
        message["Subject"] = "🏆 You did it! Your FREE book is ready - you've earned it | Pandora Pages"
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = user.email
        message.set_content(
            f"Hi {name} 👋\n\n"
            "This is amazing - 5 parents bought PandoraPages books because you shared it 💛\n"
            "That truly means a lot to us. And as promised...\n\n"
            "🎁 Your FREE Digital Book is Ready\n\n"
            "You have earned a FREE digital book - completely on us!\n\n"
            "👉 Download Your Free Book Now\n\n"
            '"You did not just earn a reward. You introduced 5 children to the joy of reading. '
            'That impact is truly special." 🌟\n'
            "- Team PandoraPages\n\n"
            "🚀 You are halfway to something BIG\n\n"
            "📊 Progress: 5 / 10 referrals\n\n"
            "You are just 5 more referrals away from a FREE personalized digital book.\n\n"
            "📱 Share and reach faster\n"
            "One simple message to your parent groups can get you there quickly.\n"
            "Every parent who uses your code = one step closer to your next reward.\n\n"
            "📚 Use your reward on these\n"
            "- Magic Forest Adventure Storybook (Now INR 99)\n"
            "- Chess in 21 Days - SkillSprint challenge book (Now INR 99)\n\n"
            "👉 Instant download - Print at home\n\n"
            "📱 Join Our Parent Community\n"
            "Free coloring pages, mini-stories and activity ideas every week.\n"
            "Join 10,000+ parents.\n\n"
            "👉 Join Free\n\n"
            f"Thank you again, {name} 💛\n"
            "You are helping bring stories, imagination, and joy into more homes - and that truly matters.\n\n"
            "With love,\n"
            "PandoraPages"
        )
        await asyncio.to_thread(self._send_email_sync, message)

    @staticmethod
    def _send_email_sync(message: EmailMessage) -> None:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
