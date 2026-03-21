'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/lib/providers/auth-provider';
import { Loader as Loader2, Sparkles, Eye, EyeOff, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import Link from 'next/link';

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
      <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-300 ${bar.w} ${bar.color}`} />
      </div>
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
            {c.pass
              ? <CheckCircle2 className="h-2.5 w-2.5" />
              : <div className="h-2.5 w-2.5 rounded-full border border-current opacity-40" />}
            {c.label}
          </span>
        ))}
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function SignupPage() {
  const { register: registerUser, isAuthenticated } = useAuth();
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm]   = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const passwordValue = watch('password', '');

  if (isAuthenticated) {
    router.push('/dashboard');
    return null;
  }

  const onSubmit = async (data: FormData) => {
    try {
      await registerUser(data.name, data.email, data.password);
      toast.success(`Welcome to PandaTales, ${data.name}! 🐼✨`);
      router.push('/dashboard');
    } catch {
      toast.error('Registration failed. Please try again.');
    }
  };

  const handleSocialSignup = (provider: string) => {
    toast.info(`${provider} sign-up is not implemented in this demo`);
  };

  return (
    <div className="min-h-screen relative">
      <main className="relative z-10 container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="max-w-md mx-auto"
        >
          <div className="text-center mb-8">
            <Sparkles className="h-16 w-16 mx-auto mb-4 text-primary sparkle" />
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-[#6B21A8] to-[#C9A227] bg-clip-text text-transparent">
              Join PandaTales
            </h1>
            <p className="text-muted-foreground">
              Create your account and start building magical books 🐼
            </p>
          </div>

          <Card className="rounded-3xl shadow-xl">
            <CardHeader>
              <CardTitle>Create Account</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                {/* Full name */}
                <div>
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    {...register('name')}
                    placeholder="e.g. Sarah Johnson"
                    autoComplete="name"
                    className="rounded-xl mt-1"
                  />
                  {errors.name && (
                    <p className="text-sm text-destructive mt-1">{errors.name.message}</p>
                  )}
                </div>

                {/* Email */}
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    {...register('email')}
                    placeholder="parent@example.com"
                    autoComplete="email"
                    className="rounded-xl mt-1"
                  />
                  {errors.email && (
                    <p className="text-sm text-destructive mt-1">{errors.email.message}</p>
                  )}
                </div>

                {/* Password */}
                <div>
                  <Label htmlFor="password">Password</Label>
                  <div className="relative mt-1">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      {...register('password')}
                      placeholder="Create a strong password"
                      autoComplete="new-password"
                      className="rounded-xl pr-10"
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
                    <p className="text-sm text-destructive mt-1">{errors.password.message}</p>
                  )}
                </div>

                {/* Confirm password */}
                <div>
                  <Label htmlFor="confirmPassword">Confirm Password</Label>
                  <div className="relative mt-1">
                    <Input
                      id="confirmPassword"
                      type={showConfirm ? 'text' : 'password'}
                      {...register('confirmPassword')}
                      placeholder="Repeat your password"
                      autoComplete="new-password"
                      className="rounded-xl pr-10"
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
                    <p className="text-sm text-destructive mt-1">{errors.confirmPassword.message}</p>
                  )}
                </div>

                <Button
                  type="submit"
                  className="w-full rounded-xl"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating your account…
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-4 w-4" />
                      Create My Account
                    </>
                  )}
                </Button>
              </form>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">Or continue with</span>
                </div>
              </div>

              <div className="space-y-3">
                <Button
                  type="button"
                  variant="outline"
                  className="w-full rounded-xl"
                  onClick={() => handleSocialSignup('Google')}
                >
                  <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                  </svg>
                  Sign up with Google
                </Button>
              </div>

              <div className="border-t mt-6 pt-5 text-center">
                <p className="text-sm text-muted-foreground">
                  Already have an account?{' '}
                  <Link
                    href="/login"
                    className="font-semibold text-[#6B21A8] hover:underline underline-offset-2 transition-colors"
                  >
                    Sign in
                  </Link>
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </main>
    </div>
  );
}
