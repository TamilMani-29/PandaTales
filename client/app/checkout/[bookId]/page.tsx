'use client';

import { useCallback, useState, useEffect, useMemo } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { useStoryBook, useColoringBook } from '@/features/books/hooks/useBooks';
import { useCreateOrder, useVerifyPayment } from '@/features/checkout/hooks/useCheckout';
import { Loader as Loader2, BookOpen, Check, Download, Printer, ShieldCheck, CheckCircle2, MessageCircle, Mail, Home, ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import Image from 'next/image';
import Link from 'next/link';
import confetti from 'canvas-confetti';
import { mockProcessPayment } from '@/lib/mock-api/mock-generation.service';

// TODO: Set to false (and remove the mock block in handleCheckout below) when
//       Razorpay keys are configured in the environment.
//       The real Razorpay flow is fully preserved — just flip this flag.
const USE_MOCK_PAYMENT = true;

type Format = 'digital' | 'softcover' | 'hardcover';

const formatOptions: {
  value: Format;
  label: string;
  price: number;
  displayPrice: string;
  description: string;
  icon: React.ReactNode;
  tag?: string;
}[] = [
  {
    value: 'digital',
    label: 'Digital Download',
    price: 49900,
    displayPrice: '₹499',
    description: 'Instant high-resolution PDF — print at home or at any print shop, unlimited times',
    icon: <Download className="h-5 w-5" />,
    tag: 'Most popular',
  },
  {
    value: 'softcover',
    label: 'Softcover Print',
    price: 129900,
    displayPrice: '₹1,299',
    description: 'Professionally printed softcover book shipped to your door in 5–7 business days',
    icon: <Printer className="h-5 w-5" />,
  },
  {
    value: 'hardcover',
    label: 'Hardcover Print',
    price: 179900,
    displayPrice: '₹1,799',
    description: 'Premium hardcover binding — ideal for gifting, ships in 5–7 business days',
    icon: <Printer className="h-5 w-5" />,
    tag: 'Best gift',
  },
];

/** Dynamically load the Razorpay checkout script */
function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (typeof window === 'undefined') return resolve(false);
    if ((window as any).Razorpay) return resolve(true);
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

export default function CheckoutPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const bookId = params.bookId as string;

  const formatParam = searchParams.get('format');
  const initialFormat: Format = formatParam === 'print' ? 'softcover' : 'digital';

  const [selectedFormat, setSelectedFormat] = useState<Format>(initialFormat);
  const [isProcessing, setIsProcessing] = useState(false);
  const [confirmedFormat, setConfirmedFormat] = useState<Format | null>(null);
  const [activeSlide, setActiveSlide] = useState(0);

  const { data: storyBook } = useStoryBook(bookId);
  const { data: coloringBook } = useColoringBook(bookId);
  const book = storyBook || coloringBook;

  const allImages = useMemo(() => {
    if (!book) return [];
    // StoryBook has coverImage + previewImages; ColoringBookTemplateListItem has coverImageUrl
    const cover = 'coverImage' in book ? book.coverImage : (book as any).coverImageUrl;
    const previews: string[] = 'previewImages' in book ? (book as any).previewImages ?? [] : [];
    return [cover, ...previews].filter(Boolean).slice(0, 5) as string[];
  }, [book]);

  useEffect(() => {
    if (allImages.length <= 1) return;
    const timer = setInterval(() => {
      setActiveSlide((prev) => (prev + 1) % allImages.length);
    }, 3000);
    return () => clearInterval(timer);
  }, [allImages.length]);

  const { mutateAsync: createOrder } = useCreateOrder();
  const { mutateAsync: verifyPayment } = useVerifyPayment();

  const handleCheckout = useCallback(async () => {
    setIsProcessing(true);
    try {
      // ── MOCK PAYMENT BLOCK ───────────────────────────────────────────────────
      // TODO: Remove this block when Razorpay keys are ready (set USE_MOCK_PAYMENT = false).
      if (USE_MOCK_PAYMENT) {
        await mockProcessPayment(selectedFormat);
        confetti({ particleCount: 120, spread: 80, origin: { y: 0.6 } });
        setConfirmedFormat(selectedFormat);
        return;
      }
      // ── END MOCK BLOCK ───────────────────────────────────────────────────────

      const loaded = await loadRazorpayScript();
      if (!loaded) {
        toast.error('Failed to load payment gateway. Please check your connection.');
        return;
      }

      // Step 1 — create Razorpay order on the server
      const order = await createOrder({
        bookId,
        format: selectedFormat,
      });

      // Step 2 — open Razorpay modal
      await new Promise<void>((resolve, reject) => {
        const rzp = new (window as any).Razorpay({
          key: order.key_id,
          order_id: order.razorpay_order_id,
          amount: order.amount,
          currency: order.currency,
          name: 'Pandora Pages',
          description: `${selectedOption.label} — ${book?.title ?? 'Your Book'}`,
          image: '/logo.png',
          handler: async (response: {
            razorpay_order_id: string;
            razorpay_payment_id: string;
            razorpay_signature: string;
          }) => {
            try {
              // Step 3 — verify and fulfil
              await verifyPayment({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              });
              confetti({ particleCount: 120, spread: 80, origin: { y: 0.6 } });
              setConfirmedFormat(selectedFormat);
              resolve();
            } catch {
              toast.error('Payment verification failed. Contact support if amount was deducted.');
              reject(new Error('verification_failed'));
            }
          },
          modal: {
            ondismiss: () => {
              toast('Payment cancelled.');
              resolve();
            },
          },
          prefill: { email: '' },
          theme: { color: '#6B21A8' },
        });
        rzp.open();
      });
    } catch (err: any) {
      if (err?.message !== 'verification_failed') {
        toast.error('Could not initiate payment. Please try again.');
      }
    } finally {
      setIsProcessing(false);
    }
  }, [bookId, selectedFormat, createOrder, verifyPayment, router, book]);

  if (!book) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[#6B21A8]" />
      </div>
    );
  }

  // ── Post-payment confirmation screen ────────────────────────────────────────
  if (confirmedFormat) {
    const isPrint = confirmedFormat !== 'digital';
    const formatLabel = confirmedFormat === 'softcover' ? 'Softcover' : confirmedFormat === 'hardcover' ? 'Hardcover' : 'Digital';
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="max-w-lg w-full"
        >
          <Card className="rounded-3xl shadow-xl border-2 border-green-100">
            <CardContent className="p-8 text-center">
              {/* Icon */}
              <div className="w-20 h-20 rounded-full bg-green-50 border-2 border-green-200 flex items-center justify-center mx-auto mb-6">
                <CheckCircle2 className="h-10 w-10 text-green-500" />
              </div>

              <h1 className="text-2xl md:text-3xl font-bold mb-2">
                {isPrint ? 'Order Placed!' : 'Payment Successful!'}
              </h1>
              <p className="text-muted-foreground mb-6">
                {isPrint
                  ? `Your ${formatLabel} print order has been received.`
                  : 'Your payment has been confirmed.'}
              </p>

              {/* Book summary strip */}
              <div className="flex items-center gap-4 bg-muted/50 rounded-2xl p-4 mb-6 text-left">
                <div className="relative w-14 h-18 flex-shrink-0 rounded-lg overflow-hidden">
                  <Image src={book.coverImage} alt={book.title} fill className="object-cover" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold truncate">{book.title}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{formatLabel} · {book.totalPages} pages</p>
                </div>
              </div>

              {/* What happens next */}
              {isPrint ? (
                <div className="rounded-2xl border-2 border-amber-200 bg-amber-50/60 p-5 text-left mb-6">
                  <div className="flex items-center gap-2 mb-3">
                    <MessageCircle className="h-5 w-5 text-amber-600 flex-shrink-0" />
                    <span className="font-semibold text-amber-800">What happens next?</span>
                  </div>
                  <ul className="space-y-2 text-sm text-amber-900">
                    <li className="flex items-start gap-2">
                      <Check className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                      We will reach out to you on WhatsApp within <strong>&nbsp;24 hours</strong> to confirm your shipping address and order details.
                    </li>
                    <li className="flex items-start gap-2">
                      <Check className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                      Your book will be professionally printed and dispatched within 2 business days of confirmation.
                    </li>
                    <li className="flex items-start gap-2">
                      <Check className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                      Estimated delivery: <strong>&nbsp;5–7 business days</strong> after dispatch.
                    </li>
                  </ul>
                </div>
              ) : (
                <div className="rounded-2xl border-2 border-[#6B21A8]/20 bg-[#6B21A8]/5 p-5 text-left mb-6">
                  <div className="flex items-center gap-2 mb-3">
                    <Mail className="h-5 w-5 text-[#6B21A8] flex-shrink-0" />
                    <span className="font-semibold text-[#6B21A8]">What happens next?</span>
                  </div>
                  <ul className="space-y-2 text-sm text-[#6B21A8]/80">
                    <li className="flex items-start gap-2">
                      <Check className="h-4 w-4 text-[#6B21A8] mt-0.5 flex-shrink-0" />
                      Your personalised PDF is being prepared right now.
                    </li>
                    <li className="flex items-start gap-2">
                      <Check className="h-4 w-4 text-[#6B21A8] mt-0.5 flex-shrink-0" />
                      It will be sent to your email shortly — check your inbox (and spam folder).
                    </li>
                    <li className="flex items-start gap-2">
                      <Check className="h-4 w-4 text-[#6B21A8] mt-0.5 flex-shrink-0" />
                      You can print it at home or at any print shop, as many times as you like.
                    </li>
                  </ul>
                </div>
              )}

              <Link href="/">
                <Button
                  size="lg"
                  className="w-full rounded-xl text-base py-6 bg-[#6B21A8] hover:bg-[#581C87] gap-2"
                >
                  <Home className="h-5 w-5" />
                  Go to Homepage
                </Button>
              </Link>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    );
  }

  const selectedOption = formatOptions.find((opt) => opt.value === selectedFormat)!;

  return (
    <div className="min-h-screen relative">
      <main className="relative z-10 container mx-auto px-4 py-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto"
        >
          <div className="text-center mb-10">
            <h1 className="text-4xl md:text-5xl font-bold mb-3 bg-gradient-to-r from-[#6B21A8] to-[#C9A227] bg-clip-text text-transparent">
              Choose Your Format
            </h1>
            <p className="text-muted-foreground text-lg">
              Select how you'd like to receive your personalised coloring book
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <Card className="rounded-3xl shadow-lg overflow-hidden sticky top-24">
                <div className="relative aspect-[3/4] overflow-hidden">
                  {allImages.map((src, idx) => (
                    <Image
                      key={idx}
                      src={src}
                      alt={`${book.title} — preview ${idx + 1}`}
                      fill
                      className={`object-cover transition-opacity duration-700 ${
                        idx === activeSlide ? 'opacity-100' : 'opacity-0'
                      }`}
                    />
                  ))}

                  {/* Prev / Next arrows */}
                  {allImages.length > 1 && (
                    <>
                      <button
                        type="button"
                        onClick={() =>
                          setActiveSlide((prev) => (prev - 1 + allImages.length) % allImages.length)
                        }
                        className="absolute left-2 top-1/2 -translate-y-1/2 z-10 bg-white/75 hover:bg-white rounded-full p-1 shadow transition-colors"
                        aria-label="Previous image"
                      >
                        <ChevronLeft className="h-4 w-4 text-foreground" />
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          setActiveSlide((prev) => (prev + 1) % allImages.length)
                        }
                        className="absolute right-2 top-1/2 -translate-y-1/2 z-10 bg-white/75 hover:bg-white rounded-full p-1 shadow transition-colors"
                        aria-label="Next image"
                      >
                        <ChevronRight className="h-4 w-4 text-foreground" />
                      </button>
                    </>
                  )}

                  {/* Dot indicators */}
                  {allImages.length > 1 && (
                    <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5 z-10">
                      {allImages.map((_, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => setActiveSlide(idx)}
                          className={`rounded-full transition-all ${
                            idx === activeSlide
                              ? 'w-4 h-2 bg-white scale-110'
                              : 'w-2 h-2 bg-white/60'
                          }`}
                          aria-label={`Go to image ${idx + 1}`}
                        />
                      ))}
                    </div>
                  )}
                </div>
                <CardContent className="p-6">
                  <h2 className="text-xl font-bold mb-1">{book.title}</h2>
                  <p className="text-muted-foreground text-sm">{book.description}</p>
                  <div className="mt-4 flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">
                      <BookOpen className="inline h-4 w-4 mr-1" />
                      {book.totalPages} pages
                    </span>
                    <span className="text-muted-foreground">Ages {book.ageGroup}</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-5">
              <Card className="rounded-3xl shadow-lg">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">Select Format</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {formatOptions.map((option) => {
                    const isSelected = selectedFormat === option.value;
                    return (
                      <motion.div key={option.value} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
                        <Label
                          htmlFor={option.value}
                          className={`flex items-start gap-4 p-4 rounded-2xl border-2 cursor-pointer transition-all ${
                            isSelected
                              ? 'border-[#6B21A8] bg-[#6B21A8]/5'
                              : 'border-border hover:border-[#6B21A8]/40'
                          }`}
                          onClick={() => setSelectedFormat(option.value)}
                        >
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                            isSelected ? 'bg-[#6B21A8] text-white' : 'bg-muted text-muted-foreground'
                          }`}>
                            {option.icon}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                              <span className="font-semibold text-sm">{option.label}</span>
                              {option.tag && (
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
                                  {option.tag}
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground leading-relaxed">{option.description}</p>
                            <p className="mt-2 font-bold text-[#6B21A8]">{option.displayPrice}</p>
                          </div>
                          {isSelected && <Check className="h-5 w-5 text-[#6B21A8] flex-shrink-0 mt-0.5" />}
                        </Label>
                      </motion.div>
                    );
                  })}
                </CardContent>
              </Card>

              <Card className="rounded-3xl shadow-lg">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-base font-semibold">Total</span>
                    <span className="text-3xl font-bold text-[#6B21A8]">{selectedOption.displayPrice}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mb-5">
                    {selectedFormat === 'digital'
                      ? 'Instant PDF delivered to your email after payment'
                      : 'We will contact you on WhatsApp after payment to confirm shipping details. Delivered in 5–7 business days.'}
                  </p>
                  <Button
                    onClick={handleCheckout}
                    disabled={isProcessing}
                    className="w-full rounded-xl text-base py-6 bg-[#6B21A8] hover:bg-[#581C87]"
                    size="lg"
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                        Processing...
                      </>
                    ) : selectedFormat === 'digital' ? (
                      <>
                        <Download className="mr-2 h-5 w-5" />
                        Buy & Download PDF
                      </>
                    ) : (
                      <>
                        <Printer className="mr-2 h-5 w-5" />
                        Place Print Order
                      </>
                    )}
                  </Button>
                  <p className="text-xs text-muted-foreground text-center mt-4 flex items-center justify-center gap-1">
                    <ShieldCheck className="h-3.5 w-3.5 text-green-600" />
                    Secured by Razorpay
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
