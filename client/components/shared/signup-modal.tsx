'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/lib/providers/auth-provider';
import { toast } from 'sonner';
import {
  Loader2,
  Sparkles,
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  CircleAlert as AlertCircle,
  CheckCircle2,
} from 'lucide-react';

// ── Validation ────────────────────────────────────────────────────────────────

const schema = z
  .object({
    name: z.string().min(2, 'Name must be at least 2 characters').max(60),
    email: z.string().email('Please enter a valid email address'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
      .regex(/[0-9]/, 'Must contain at least one number'),
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type FormData = z.infer<typeof schema>;

// ── Password strength indicator ───────────────────────────────────────────────

function PasswordStrength({ password }: { password: string }) {
  const checks = [
    { label: '8+ characters',    pass: password.length >= 8 },
    { label: 'Uppercase letter', pass: /[A-Z]/.test(password) },
    { label: 'Number',           pass: /[0-9]/.test(password) },
  ];

  if (!password) return null;

  const strength = checks.filter((c) => c.pass).length;
  const bar = [
    { w: 'w-1/3', color: 'bg-red-400' },
    { w: 'w-2/3', color: 'bg-amber-400' },
    { w: 'w-full', color: 'bg-green-500' },
  ][strength - 1] ?? { w: 'w-0', color: '' };

  return (
    <div className="mt-2 space-y-2">
      {/* Strength bar */}
      <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-300 ${bar.w} ${bar.color}`} />
      </div>
      {/* Criteria chips */}
      <div className="flex flex-wrap gap-1.5">
        {checks.map((c) => (
          <span
            key={c.label}
            className={`inline-flex items-center gap-1 text-[11px] rounded-full px-2 py-0.5 font-medium transition-colors ${
              c.pass
                ? 'bg-green-50 text-green-700 border border-green-200'
                : 'bg-muted text-muted-foreground border border-transparent'
            }`}
          >
            {c.pass ? <CheckCircle2 className="h-2.5 w-2.5" /> : <div className="h-2.5 w-2.5 rounded-full border border-current opacity-40" />}
            {c.label}
          </span>
        ))}
      </div>
    </div>
  );
}

// ── Props ─────────────────────────────────────────────────────────────────────

interface SignupModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSwitchToLogin?: () => void;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function SignupModal({ open, onOpenChange, onSwitchToLogin }: SignupModalProps) {
  const { register: registerUser } = useAuth();
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm]   = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const passwordValue = watch('password', '');

  const onSubmit = async (data: FormData) => {
    try {
      await registerUser(data.name, data.email, data.password);
      toast.success(`Welcome to PandaTales, ${data.name}! 🐼✨`);
      reset();
      onOpenChange(false);
      router.push('/dashboard');
    } catch {
      toast.error('Registration failed. Please try again.');
    }
  };

  const handleSwitchToLogin = () => {
    reset();
    onOpenChange(false);
    onSwitchToLogin?.();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) reset(); onOpenChange(v); }}>
      <DialogContent className="sm:max-w-md rounded-3xl p-0 overflow-hidden gap-0">
        {/* Decorative header banner */}
        <div className="bg-gradient-to-br from-[#6B21A8] via-violet-600 to-[#C9A227] px-7 pt-8 pb-6 relative overflow-hidden">
          {/* Background sparkles */}
          <div className="absolute top-3 right-6 opacity-30 text-white text-2xl select-none">✨</div>
          <div className="absolute bottom-4 left-6 opacity-20 text-white text-lg select-none">⭐</div>
          <div className="absolute top-6 left-1/2 opacity-10 text-white text-3xl select-none">🌟</div>

          <div className="relative z-10 flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-white/20 flex items-center justify-center shadow-inner">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            <div>
              <DialogTitle className="text-white text-xl font-bold leading-tight">
                Create your account
              </DialogTitle>
              <DialogDescription className="text-white/75 text-sm mt-0.5">
                Join PandaTales and start creating magical books 🐼
              </DialogDescription>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="px-7 py-6 space-y-4">

          {/* Full name */}
          <div>
            <Label htmlFor="signup-name" className="flex items-center gap-1.5 text-sm font-semibold mb-1.5">
              <User className="h-3.5 w-3.5 text-purple-500" />
              Full Name
            </Label>
            <Input
              id="signup-name"
              {...register('name')}
              placeholder="e.g. Sarah Johnson"
              autoComplete="name"
              className="rounded-xl border-purple-100 focus:border-purple-300 focus-visible:ring-purple-200"
            />
            {errors.name && (
              <p className="text-xs text-destructive mt-1 flex items-center gap-1">
                <AlertCircle className="h-3 w-3 flex-shrink-0" />
                {errors.name.message}
              </p>
            )}
          </div>

          {/* Email */}
          <div>
            <Label htmlFor="signup-email" className="flex items-center gap-1.5 text-sm font-semibold mb-1.5">
              <Mail className="h-3.5 w-3.5 text-purple-500" />
              Email Address
            </Label>
            <Input
              id="signup-email"
              type="email"
              {...register('email')}
              placeholder="parent@example.com"
              autoComplete="email"
              className="rounded-xl border-purple-100 focus:border-purple-300 focus-visible:ring-purple-200"
            />
            {errors.email && (
              <p className="text-xs text-destructive mt-1 flex items-center gap-1">
                <AlertCircle className="h-3 w-3 flex-shrink-0" />
                {errors.email.message}
              </p>
            )}
          </div>

          {/* Password */}
          <div>
            <Label htmlFor="signup-password" className="flex items-center gap-1.5 text-sm font-semibold mb-1.5">
              <Lock className="h-3.5 w-3.5 text-purple-500" />
              Password
            </Label>
            <div className="relative">
              <Input
                id="signup-password"
                type={showPassword ? 'text' : 'password'}
                {...register('password')}
                placeholder="Create a strong password"
                autoComplete="new-password"
                className="rounded-xl border-purple-100 focus:border-purple-300 focus-visible:ring-purple-200 pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                tabIndex={-1}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <PasswordStrength password={passwordValue} />
            {errors.password && (
              <p className="text-xs text-destructive mt-1 flex items-center gap-1">
                <AlertCircle className="h-3 w-3 flex-shrink-0" />
                {errors.password.message}
              </p>
            )}
          </div>

          {/* Confirm password */}
          <div>
            <Label htmlFor="signup-confirm" className="flex items-center gap-1.5 text-sm font-semibold mb-1.5">
              <Lock className="h-3.5 w-3.5 text-purple-500" />
              Confirm Password
            </Label>
            <div className="relative">
              <Input
                id="signup-confirm"
                type={showConfirm ? 'text' : 'password'}
                {...register('confirmPassword')}
                placeholder="Repeat your password"
                autoComplete="new-password"
                className="rounded-xl border-purple-100 focus:border-purple-300 focus-visible:ring-purple-200 pr-10"
              />
              <button
                type="button"
                onClick={() => setShowConfirm((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                tabIndex={-1}
                aria-label={showConfirm ? 'Hide password' : 'Show password'}
              >
                {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {errors.confirmPassword && (
              <p className="text-xs text-destructive mt-1 flex items-center gap-1">
                <AlertCircle className="h-3 w-3 flex-shrink-0" />
                {errors.confirmPassword.message}
              </p>
            )}
          </div>

          {/* Submit */}
          <Button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-xl py-5 text-sm font-bold bg-gradient-to-r from-[#6B21A8] to-violet-600 hover:from-[#581C87] hover:to-violet-700 shadow-md shadow-purple-200 transition-all hover:shadow-purple-300 hover:scale-[1.01] disabled:opacity-60 disabled:scale-100 disabled:shadow-none mt-1"
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Creating your account…
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                Create My Account
              </span>
            )}
          </Button>

          {/* Switch to login */}
          <p className="text-center text-sm text-muted-foreground pt-1">
            Already have an account?{' '}
            <button
              type="button"
              onClick={handleSwitchToLogin}
              className="font-semibold text-[#6B21A8] hover:underline underline-offset-2 transition-colors"
            >
              Sign in
            </button>
          </p>
        </form>
      </DialogContent>
    </Dialog>
  );
}
