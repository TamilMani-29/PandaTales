'use client';

import { useMemo, useState } from 'react';
import confetti from 'canvas-confetti';
import { motion } from 'framer-motion';
import { Mail, MessageCircleMore, Send, Sparkles } from 'lucide-react';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useSendDigitalBookToEmail } from '@/features/digital-books/hooks/useDigitalBooks';
import { DigitalBook } from '@/features/digital-books/types/digital-book.types';

interface BuyDigitalBookModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  book: DigitalBook;
}

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function BuyDigitalBookModal({ open, onOpenChange, book }: BuyDigitalBookModalProps) {
  const [deliveryMethod, setDeliveryMethod] = useState<'email' | 'whatsapp'>('email');
  const [email, setEmail] = useState('');
  const [emailTouched, setEmailTouched] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const mutation = useSendDigitalBookToEmail();
  const isValidEmail = useMemo(() => emailRegex.test(email.trim()), [email]);

  const resetState = () => {
    setDeliveryMethod('email');
    setEmail('');
    setEmailTouched(false);
    setIsSuccess(false);
    mutation.reset();
  };

  const close = (nextOpen: boolean) => {
    if (!nextOpen) resetState();
    onOpenChange(nextOpen);
  };

  const submit = async () => {
    setEmailTouched(true);
    if (!isValidEmail) return;

    await mutation.mutateAsync({
      bookId: book.id,
      email: email.trim(),
    });

    setIsSuccess(true);
    confetti({
      particleCount: 120,
      spread: 80,
      origin: { y: 0.7 },
      zIndex: 2000,
    });
  };

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent className="rounded-2xl border-blue-100 sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl text-slate-900">Buy Book</DialogTitle>
          <DialogDescription>
            Receive <span className="font-medium text-blue-700">{book.bookName}</span> instantly after payment.
          </DialogDescription>
        </DialogHeader>

        {isSuccess ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.28, ease: 'easeOut' }}
            className="space-y-3 rounded-xl bg-gradient-to-br from-blue-50 to-cyan-50 p-6 text-center"
          >
            <motion.div
              initial={{ scale: 0.7, rotate: -12 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 260, damping: 18, delay: 0.08 }}
              className="mx-auto inline-flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white"
            >
              <Sparkles className="h-5 w-5" />
            </motion.div>
            <h3 className="text-lg font-semibold text-slate-900">Book Sent Successfully</h3>
            <p className="mx-auto max-w-sm text-sm leading-relaxed text-slate-600">
              Your digital book has been sent to your email. Please check your inbox and spam folder.
            </p>
            <Button className="mt-2 w-full rounded-xl bg-blue-600 hover:bg-blue-700" onClick={() => close(false)}>
              OK
            </Button>
          </motion.div>
        ) : (
          <div className="space-y-4">
            <div>
              <p className="mb-3 text-sm font-medium text-slate-700">Receive book via:</p>
              <div className="grid grid-cols-2 gap-3">
                <Button
                  type="button"
                  variant={deliveryMethod === 'email' ? 'default' : 'outline'}
                  className="h-11 rounded-xl"
                  onClick={() => setDeliveryMethod('email')}
                >
                  <Mail className="mr-2 h-4 w-4" />
                  Email
                </Button>

                <Button type="button" variant="outline" className="h-11 cursor-not-allowed rounded-xl opacity-60" disabled>
                  <MessageCircleMore className="mr-2 h-4 w-4" />
                  WhatsApp Soon
                </Button>
              </div>
            </div>

            {deliveryMethod === 'email' && (
              <div className="space-y-2">
                <Label htmlFor="digital-book-email">Email ID</Label>
                <Input
                  id="digital-book-email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onBlur={() => setEmailTouched(true)}
                  placeholder="name@example.com"
                  className="h-11 rounded-xl"
                />
                {emailTouched && !isValidEmail ? (
                  <p className="text-xs text-red-600">Please enter a valid email address.</p>
                ) : null}
              </div>
            )}

            {mutation.isError ? (
              <p className="text-sm text-red-600">
                {(mutation.error as any)?.response?.data?.error?.message || 'Unable to send email right now. Please try again.'}
              </p>
            ) : null}

            <Button
              className="h-11 w-full rounded-xl bg-blue-600 hover:bg-blue-700"
              onClick={submit}
              disabled={mutation.isPending}
            >
              {mutation.isPending ? 'Processing...' : 'Confirm & Send'}
              <Send className="ml-2 h-4 w-4" />
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
