'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useBookPreview } from '@/features/books/hooks/useBooks';
import {
  Loader2,
  Sparkles,
  CheckCircle2,
  ImageIcon,
  BookOpen,
  AlertCircle,
  ShoppingCart,
  ArrowLeft,
  Download,
  Printer,
  ChevronLeft,
  ChevronRight,
  Clock,
} from 'lucide-react';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { Progress } from '@/components/ui/progress';
import { Footer } from '@/components/layout/footer';

export default function PreviewPage() {
  const params = useParams();
  const router = useRouter();
  const bookId = params.bookId as string;

  const { data: preview, isLoading, isError } = useBookPreview(bookId);

  const [activeSlide, setActiveSlide] = useState(0);
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [pendingNav, setPendingNav] = useState<string | null>(null);

  const isCompleted = preview?.status === 'completed';

  // Browser back / refresh / tab close guard
  useEffect(() => {
    if (!isCompleted) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = '';
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [isCompleted]);

  // In-app link click guard (intercepts header links, etc.)
  useEffect(() => {
    if (!isCompleted) return;
    const handler = (e: MouseEvent) => {
      const anchor = (e.target as HTMLElement).closest('a');
      if (!anchor) return;
      const href = anchor.getAttribute('href');
      if (!href) return;
      // Allow checkout — that is the intended next step
      if (href.startsWith(`/checkout/${bookId}`)) return;
      e.preventDefault();
      e.stopPropagation();
      setPendingNav(href);
      setShowLeaveModal(true);
    };
    document.addEventListener('click', handler, true);
    return () => document.removeEventListener('click', handler, true);
  }, [isCompleted, bookId]);

  const handleLeaveConfirm = () => {
    setShowLeaveModal(false);
    if (pendingNav) router.push(pendingNav);
  };

  const handleLeaveCancel = () => {
    setShowLeaveModal(false);
    setPendingNav(null);
  };

  useEffect(() => {
    const pages = preview?.previewPages ?? [];
    if (pages.length <= 1) return;
    const timer = setInterval(() => {
      setActiveSlide((prev) => (prev + 1) % pages.length);
    }, 3000);
    return () => clearInterval(timer);
  }, [preview?.previewPages?.length]);

  // ── Loading / error states ────────────────────────────────────────────────

  if (isLoading && !preview) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-10 w-10 animate-spin text-[#6B21A8] mx-auto" />
          <p className="text-muted-foreground font-medium">Loading your book…</p>
        </div>
      </div>
    );
  }

  if (isError || !preview) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <AlertCircle className="h-10 w-10 text-destructive mx-auto" />
          <p className="text-muted-foreground font-medium">Book not found or an error occurred.</p>
          <Link href="/story-books">
            <Button variant="outline">Browse Story Books</Button>
          </Link>
        </div>
      </div>
    );
  }

  // ── Pending / processing state ────────────────────────────────────────────

  if (preview.status === 'queued' || preview.status === 'processing') {
    const isRateLimited = preview.currentStep === 'rate_limited';

    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-6 max-w-sm px-4">
          <div className="relative mx-auto w-20 h-20">
            {isRateLimited ? (
              <>
                <div className="w-20 h-20 rounded-full bg-amber-100 flex items-center justify-center">
                  <Clock className="h-10 w-10 text-amber-500" />
                </div>
              </>
            ) : (
              <>
                <BookOpen className="h-20 w-20 text-[#6B21A8]/20" />
                <Loader2 className="h-8 w-8 animate-spin text-[#6B21A8] absolute inset-0 m-auto" />
              </>
            )}
          </div>
          <div>
            {isRateLimited ? (
              <>
                <h2 className="text-xl font-bold mb-1 text-amber-700">
                  AI Service Is Busy
                </h2>
                <p className="text-muted-foreground text-sm">
                  The image generation service is temporarily at capacity.
                  We&apos;re automatically retrying —{' '}
                  <span className="font-semibold">no action needed on your end.</span>
                  <br />
                  This page will update automatically when ready.
                </p>
              </>
            ) : (
              <>
                <h2 className="text-xl font-bold mb-1">
                  {preview.status === 'queued' ? 'In Queue…' : 'Generating Your Book…'}
                </h2>
                <p className="text-muted-foreground text-sm">
                  We&apos;re personalising{' '}
                  <span className="font-semibold">&ldquo;{preview.templateTitle}&rdquo;</span> for{' '}
                  <span className="font-semibold">{preview.childName}</span>.
                  <br />
                  This usually takes 30–60 seconds.
                </p>
              </>
            )}
          </div>
          {preview.progress > 0 && (
            <div className="space-y-2">
              <Progress value={preview.progress} className="h-2" />
              <p className="text-xs text-muted-foreground">{preview.progress}% complete</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── Failed state ──────────────────────────────────────────────────────────

  if (preview.status === 'failed' || preview.status === 'cancelled') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <AlertCircle className="h-10 w-10 text-destructive mx-auto" />
          <p className="text-lg font-semibold">Book generation failed.</p>
          <p className="text-muted-foreground text-sm">Please try again.</p>
          <Link href="/story-books">
            <Button variant="outline">Browse Story Books</Button>
          </Link>
        </div>
      </div>
    );
  }

  // ── Completed state ───────────────────────────────────────────────────────

  const isStoryBook = preview.templateType === 'story_book';
  const bookLabel = isStoryBook ? 'story book' : 'coloring book';

  return (
    <div className="min-h-screen relative">
      <main className="relative z-10 container mx-auto px-4 py-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-5xl mx-auto"
        >
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 bg-green-50 text-green-700 text-sm font-semibold px-4 py-2 rounded-full border border-green-200 mb-4">
              <CheckCircle2 className="h-4 w-4" />
              Your {bookLabel} is ready!
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-3 bg-gradient-to-r from-[#6B21A8] to-[#C9A227] bg-clip-text text-transparent">
              Preview Your Book
            </h1>
            <p className="text-muted-foreground text-lg max-w-xl mx-auto">
              {preview.previewPages.length > 0
                ? `Here are ${preview.previewPages.length} sample pages from your ${preview.totalPages}-page personalised ${bookLabel}`
                : `Your personalised ${bookLabel} – ${preview.totalPages} pages – is ready to purchase.`}
            </p>
          </div>

          {preview.previewPages.length > 0 ? (
            <div className="mb-10 max-w-sm mx-auto">
              {/* Carousel */}
              <div className="relative rounded-3xl overflow-hidden shadow-xl aspect-[3/4] bg-muted">
                {preview.previewPages.map((page, index) => (
                  <div
                    key={index}
                    className={`absolute inset-0 transition-opacity duration-700 ${
                      index === activeSlide ? 'opacity-100' : 'opacity-0'
                    }`}
                  >
                    <Image
                      src={page}
                      alt={`Preview page ${index + 1}`}
                      fill
                      className="object-cover"
                      unoptimized
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                    <div className="absolute bottom-4 left-4">
                      <span className="text-white text-xs font-semibold bg-black/30 backdrop-blur-sm px-3 py-1 rounded-full">
                        Page {index + 1} of {preview.totalPages}
                      </span>
                    </div>
                  </div>
                ))}

                {/* Prev / Next */}
                {preview.previewPages.length > 1 && (
                  <>
                    <button
                      onClick={() =>
                        setActiveSlide(
                          (prev) => (prev - 1 + preview.previewPages.length) % preview.previewPages.length
                        )
                      }
                      className="absolute left-3 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-black/60 text-white rounded-full p-2 z-10 transition-colors"
                      aria-label="Previous page"
                    >
                      <ChevronLeft className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() =>
                        setActiveSlide((prev) => (prev + 1) % preview.previewPages.length)
                      }
                      className="absolute right-3 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-black/60 text-white rounded-full p-2 z-10 transition-colors"
                      aria-label="Next page"
                    >
                      <ChevronRight className="h-5 w-5" />
                    </button>
                  </>
                )}

                {/* Dot indicators */}
                {preview.previewPages.length > 1 && (
                  <div className="absolute bottom-4 right-4 flex gap-1.5 z-10">
                    {preview.previewPages.map((_, idx) => (
                      <button
                        key={idx}
                        onClick={() => setActiveSlide(idx)}
                        className={`w-2 h-2 rounded-full transition-all duration-300 ${
                          idx === activeSlide ? 'bg-white scale-125' : 'bg-white/50'
                        }`}
                        aria-label={`Go to page ${idx + 1}`}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* More pages note */}
              {preview.totalPages > preview.previewPages.length && (
                <div className="mt-3 flex items-center justify-center gap-2 text-sm text-muted-foreground">
                  <ImageIcon className="h-4 w-4 flex-shrink-0" />
                  <span>+{preview.totalPages - preview.previewPages.length} more pages in the full book</span>
                </div>
              )}
            </div>
          ) : (
            /* No preview pages yet (generated but pages not returned) */
            <div className="flex justify-center mb-10">
              <Card className="rounded-2xl border-2 border-dashed border-border p-10 text-center max-w-sm">
                <ImageIcon className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                <p className="font-semibold text-muted-foreground">
                  Preview pages are being prepared
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  They will appear here shortly.
                </p>
              </Card>
            </div>
          )}

          {/* Purchase CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="rounded-3xl shadow-xl border-2 border-[#6B21A8]/10 bg-gradient-to-br from-white to-amber-50/40">
              <CardContent className="p-8">
                <div className="text-center mb-8">
                  <h2 className="text-2xl md:text-3xl font-bold mb-2">
                    Get Your Complete {isStoryBook ? 'Story' : 'Coloring'} Book
                  </h2>
                  <p className="text-muted-foreground">
                    All {preview.totalPages} personalised pages, ready{' '}
                    {isStoryBook ? 'to read' : 'to color'} — your way
                  </p>
                </div>

                <div className="grid md:grid-cols-2 gap-5 mb-8">
                  <div className="rounded-2xl border-2 border-[#6B21A8]/20 bg-white p-5 flex flex-col gap-3">
                    <div className="w-10 h-10 rounded-xl bg-[#6B21A8]/10 flex items-center justify-center">
                      <Download className="h-5 w-5 text-[#6B21A8]" />
                    </div>
                    <div>
                      <h3 className="font-bold text-base">Digital Download</h3>
                      <p className="text-sm text-muted-foreground mt-0.5">
                        Instant PDF — print at home or on any device, as many times as you like
                      </p>
                    </div>
                    <ul className="space-y-1.5 mt-auto">
                      {[
                        'Instant access after purchase',
                        'Print at home or at a print shop',
                        'All pages in high resolution',
                      ].map((item) => (
                        <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                          <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="rounded-2xl border-2 border-[#C9A227]/30 bg-amber-50/40 p-5 flex flex-col gap-3">
                    <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
                      <Printer className="h-5 w-5 text-[#C9A227]" />
                    </div>
                    <div>
                      <h3 className="font-bold text-base">Printed &amp; Delivered</h3>
                      <p className="text-sm text-muted-foreground mt-0.5">
                        A professionally printed and bound book shipped to your door
                      </p>
                    </div>
                    <ul className="space-y-1.5 mt-auto">
                      {[
                        'Premium soft or hardcover binding',
                        'Professional print quality',
                        'Ships in 5–7 business days',
                      ].map((item) => (
                        <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                          <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Link href={`/checkout/${bookId}`} className="flex-1 sm:flex-none">
                    <Button
                      size="lg"
                      className="w-full sm:w-auto rounded-2xl px-8 py-6 text-base bg-[#6B21A8] hover:bg-[#581C87] gap-2"
                    >
                      <ShoppingCart className="h-5 w-5" />
                      Proceed to Checkout
                    </Button>
                  </Link>
                  <Button
                    size="lg"
                    variant="outline"
                    className="flex-1 sm:flex-none w-full sm:w-auto rounded-2xl px-8 py-6 text-base gap-2"
                    onClick={() => { setPendingNav('/story-books'); setShowLeaveModal(true); }}
                  >
                    <ArrowLeft className="h-5 w-5" />
                    Cancel
                  </Button>
                </div>

                <p className="text-center text-xs text-muted-foreground mt-5">
                  <Sparkles className="inline h-3.5 w-3.5 mr-1 text-[#C9A227]" />
                  Every page features{' '}
                  {preview.childName ? `${preview.childName} as` : 'your child as'} the star of the story
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      </main>

      <Footer />

      {/* Leave confirmation modal */}
      {showLeaveModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={handleLeaveCancel}>
          <Card
            className="max-w-sm w-full rounded-3xl shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <CardContent className="p-8 flex flex-col items-center text-center gap-4">
              <div className="w-14 h-14 rounded-full bg-amber-100 flex items-center justify-center">
                <AlertCircle className="h-7 w-7 text-amber-500" />
              </div>
              <div>
                <h2 className="text-xl font-bold mb-1">Leave this page?</h2>
                <p className="text-sm text-muted-foreground">
                  Your generated book preview will be lost if you navigate away without
                  proceeding to checkout. Are you sure you want to leave?
                </p>
              </div>
              <div className="flex gap-3 w-full pt-1">
                <Button
                  variant="outline"
                  className="flex-1 rounded-2xl"
                  onClick={handleLeaveCancel}
                >
                  Stay on page
                </Button>
                <Button
                  className="flex-1 rounded-2xl bg-[#6B21A8] hover:bg-[#581C87]"
                  onClick={handleLeaveConfirm}
                >
                  Leave anyway
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
