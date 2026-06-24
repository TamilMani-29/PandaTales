"""Quick setup script for PandaTales backend"""

import asyncio
import sys
from pathlib import Path


def print_step(step: int, message: str):
    """Print a numbered step"""
    print(f"\n{'='*60}")
    print(f"Step {step}: {message}")
    print('='*60)


def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message: str):
    """Print info message"""
    print(f"ℹ️  {message}")


def check_file_exists(file_path: str) -> bool:
    """Check if a file exists"""
    return Path(file_path).exists()


def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("🚀 PandaTales Backend Setup")
    print("="*60)

    # Step 1: Check .env file
    print_step(1, "Checking environment configuration")
    if not check_file_exists(".env"):
        print_error(".env file not found!")
        print_info("Creating .env from template...")
        if check_file_exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print_success(".env file created")
            print_info("Please edit .env file with your configuration")
        else:
            print_error(".env.example not found!")
            return False
    else:
        print_success(".env file exists")

    # Step 2: Check Python version
    print_step(2, "Checking Python version")
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor >= 11:
        print_success(f"Python {python_version.major}.{python_version.minor} detected")
    else:
        print_error(f"Python 3.11+ required, but found {python_version.major}.{python_version.minor}")
        return False

    # Step 3: Check dependencies
    print_step(3, "Checking dependencies")
    try:
        import fastapi
        import sqlalchemy
        import alembic
        print_success("Core dependencies installed")
    except ImportError as e:
        print_error(f"Missing dependency: {e.name}")
        print_info("Run: uv pip install -e \".[dev]\"")
        return False

    print_step(4, "Setup Instructions")
    print("\n📝 Next Steps:\n")
    print("1. Configure .env file with your settings")
    print("   - DATABASE_URL")
    print("   - MINIO credentials")
    print("   - JWT_SECRET_KEY")
    print()
    print("2. Start services with Docker:")
    print("   docker-compose up -d")
    print()
    print("3. Run database migrations:")
    print("   alembic upgrade head")
    print()
    print("4. Initialize MinIO bucket:")
    print("   python scripts/init_minio.py")
    print()
    print("5. Start development server:")
    print("   uvicorn app.main:app --reload")
    print()
    print("6. Access API documentation:")
    print("   http://localhost:8000/docs")
    print()

    print("\n" + "="*60)
    print("✅ Setup check completed!")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
