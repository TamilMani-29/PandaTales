'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Loader2, ShoppingCart, Star } from 'lucide-react';
import { useParams } from 'next/navigation';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { BuyDigitalBookModal } from '@/features/digital-books/components/buy-digital-book-modal';
import { useDigitalBookDetails } from '@/features/digital-books/hooks/useDigitalBooks';

export default function DigitalBookDetailsPage() {
  const params = useParams<{ bookId: string }>();
  const bookId = useMemo(() => Number(params?.bookId || 0), [params]);
  const [buyOpen, setBuyOpen] = useState(false);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [reviews, setReviews] = useState<Array<{ rating: number; comment: string }>>([]);

  const { data: book, isLoading, isError } = useDigitalBookDetails(bookId);

  const submitReview = () => {
    const trimmed = comment.trim();
    if (!trimmed || rating === 0) return;

    setReviews((prev) => [{ rating, comment: trimmed }, ...prev]);
    setComment('');
    setRating(0);
  };

  if (isLoading) {
    return (
      <div className="fixed inset-x-0 bottom-0 top-16 bg-gradient-to-b from-[#eef3ff] via-[#f9fbff] to-[#eefcfb]">
        <div className="container mx-auto flex h-full items-center justify-center px-4">
          <Loader2 className="mr-2 h-5 w-5 animate-spin text-blue-700" />
          <span className="text-sm text-slate-600">Loading details...</span>
        </div>
      </div>
    );
  }

  if (isError || !book) {
    return (
      <div className="fixed inset-x-0 bottom-0 top-16 bg-gradient-to-b from-[#eef3ff] via-[#f9fbff] to-[#eefcfb]">
        <div className="container mx-auto px-4 py-10">
          <Button asChild variant="outline" className="mb-6 w-fit rounded-xl border-blue-200 bg-white/80 text-blue-700 hover:bg-blue-50">
            <Link href="/digital-books">
              <ArrowLeft className="mr-1 h-4 w-4" />
              Back to digital books
            </Link>
          </Button>
          <Card className="rounded-2xl border-red-100 bg-red-50/70">
            <CardContent className="p-6 text-red-700">Unable to load this book. Please try again later.</CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-x-0 bottom-0 top-16 overflow-hidden bg-gradient-to-b from-[#eef3ff] via-[#f9fbff] to-[#eefcfb]">
      <main className="container mx-auto flex h-full flex-col px-4 py-5 md:py-6">
        <Button asChild variant="outline" className="mb-6 w-fit rounded-xl border-blue-200 bg-white/80 text-blue-700 hover:bg-blue-50">
          <Link href="/digital-books">
            <ArrowLeft className="mr-1 h-4 w-4" />
            Back to digital books
          </Link>
        </Button>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="min-h-0 flex-1 grid gap-5 lg:grid-cols-[360px_1fr]">
          <Card className="overflow-hidden rounded-3xl border-blue-100/80 bg-white/90 shadow-[0_12px_30px_rgba(37,99,235,0.10)] backdrop-blur">
            <div className="relative h-full min-h-[520px] bg-gradient-to-b from-slate-50 via-white to-blue-50">
              <Image
                src={book.coverImagePresignedUrl || '/logo_without_name.png'}
                alt={book.bookName}
                fill
                className="object-contain object-center p-2"
                unoptimized
              />
            </div>
          </Card>

          <Card className="rounded-3xl border-blue-100/80 bg-white/95 shadow-[0_12px_30px_rgba(15,23,42,0.08)]">
            <CardContent className="flex h-full min-h-0 flex-col gap-4 p-5 md:p-6">
              <div>
                <h1 className="text-3xl font-extrabold uppercase tracking-wide text-slate-900 md:text-4xl">{book.bookName}</h1>
                <p className="mt-1 text-sm text-slate-600">{book.genreName || 'General'}</p>
              </div>

              <div className="grid grid-cols-2 gap-3 rounded-2xl border border-slate-200/80 bg-gradient-to-br from-slate-50 to-blue-50/40 p-4 text-sm shadow-inner">
                <div>
                  <p className="text-slate-500">Genre</p>
                  <p className="font-medium text-slate-900">{book.genreName || 'General'}</p>
                </div>
                <div>
                  <p className="text-slate-500">Style</p>
                  <p className="font-medium text-slate-900">{book.style || 'Creative'}</p>
                </div>
                <div>
                  <p className="text-slate-500">Age Group</p>
                  <p className="font-medium text-slate-900">{book.ageGroup || '-'}</p>
                </div>
                <div>
                  <p className="text-slate-500">Total Pages</p>
                  <p className="font-medium text-slate-900">{book.totalPages || '-'}</p>
                </div>
                <div>
                  <p className="text-slate-500">Language</p>
                  <p className="font-medium text-slate-900">{book.language || 'english'}</p>
                </div>
                <div>
                  <p className="text-slate-500">Downloads</p>
                  <p className="font-medium text-slate-900">{book.downloadCount}</p>
                </div>
                <div>
                  <p className="text-slate-500">Rating</p>
                  <p className="font-medium text-slate-900">{book.rating.toFixed(1)} / 5</p>
                </div>
                <div>
                  <p className="text-slate-500">Total Ratings</p>
                  <p className="font-medium text-slate-900">{book.totalRatings}</p>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">Comments & Reviews</h2>
                <div className="flex flex-wrap items-center justify-end gap-3">
                  <Button variant="outline" className="rounded-xl border-slate-300 bg-white/80" disabled>
                    <ShoppingCart className="mr-2 h-4 w-4" />
                    Add to Cart
                  </Button>
                  <Button className="rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700" onClick={() => setBuyOpen(true)}>
                    Buy Book
                  </Button>
                </div>
              </div>

              <div className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
                <div className="rounded-2xl border border-slate-200/90 bg-white/95 p-4 shadow-sm">
                  <p className="mb-2 text-sm font-semibold text-slate-700">Rate this book</p>
                  <div className="mb-3 flex items-center gap-1">
                    {Array.from({ length: 5 }).map((_, idx) => {
                      const value = idx + 1;
                      const active = value <= rating;
                      return (
                        <button
                          key={value}
                          type="button"
                          onClick={() => setRating(value)}
                          className="rounded p-1 transition-colors hover:bg-amber-50"
                          aria-label={`Rate ${value} star${value > 1 ? 's' : ''}`}
                        >
                          <Star className={`h-5 w-5 ${active ? 'fill-amber-400 text-amber-400' : 'text-slate-300'}`} />
                        </button>
                      );
                    })}
                  </div>

                  <Textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Write your review about this book..."
                    className="min-h-[90px] rounded-xl border-slate-300/80 bg-slate-50/70"
                  />

                  <div className="mt-3 flex justify-end">
                    <Button
                      className="rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                      onClick={submitReview}
                      disabled={rating === 0 || !comment.trim()}
                    >
                      Submit Review
                    </Button>
                  </div>
                </div>

                {reviews.length > 0 ? (
                  <div className="space-y-2">
                    {reviews.map((review, idx) => (
                      <div key={`${review.comment}-${idx}`} className="rounded-xl border border-slate-200/90 bg-white p-3 shadow-sm">
                        <div className="mb-1 flex items-center gap-0.5">
                          {Array.from({ length: 5 }).map((_, i) => (
                            <Star
                              key={i}
                              className={`h-3.5 w-3.5 ${i < review.rating ? 'fill-amber-400 text-amber-400' : 'text-slate-300'}`}
                            />
                          ))}
                        </div>
                        <p className="text-sm text-slate-700">{review.comment}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">No reviews yet. Be the first to review this book.</p>
                )}
              </div>

            </CardContent>
          </Card>
        </motion.div>
      </main>

      <BuyDigitalBookModal open={buyOpen} onOpenChange={setBuyOpen} book={book} />
    </div>
  );
}
