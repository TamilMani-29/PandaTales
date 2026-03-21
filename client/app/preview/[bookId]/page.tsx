'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useBookPreview } from '@/features/books/hooks/useBooks';
import { Loader as Loader2, Download, Printer, Sparkles, CircleCheck as CheckCircle2, Image as ImageIcon } from 'lucide-react';
import Image from 'next/image';
import { motion } from 'framer-motion';

export default function PreviewPage() {
  const params = useParams();
  const bookId = params.bookId as string;

  const { data: preview, isLoading } = useBookPreview(bookId);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-10 w-10 animate-spin text-[#6B21A8] mx-auto" />
          <p className="text-muted-foreground font-medium">Generating your personalised pages...</p>
          <p className="text-sm text-muted-foreground">This usually takes 30–60 seconds</p>
        </div>
      </div>
    );
  }

  if (!preview) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-lg text-muted-foreground">Book preview not found</p>
      </div>
    );
  }

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
              Your coloring book is ready!
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-3 bg-gradient-to-r from-[#6B21A8] to-[#C9A227] bg-clip-text text-transparent">
              Preview Your Book
            </h1>
            <p className="text-muted-foreground text-lg max-w-xl mx-auto">
              Here are {preview.previewPages.length} sample pages from your {preview.totalPages}-page personalised coloring book
            </p>
          </div>

          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-5 mb-10">
            {preview.previewPages.map((page, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.08 }}
              >
                <Card className="overflow-hidden rounded-2xl shadow-md group">
                  <div className="relative aspect-[3/4]">
                    <Image
                      src={page}
                      alt={`Preview page ${index + 1}`}
                      fill
                      className="object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                    <div className="absolute bottom-3 left-3">
                      <span className="text-white text-xs font-semibold bg-black/30 backdrop-blur-sm px-2 py-1 rounded-full">
                        Page {index + 1}
                      </span>
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}

            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: preview.previewPages.length * 0.08 }}
            >
              <Card className="overflow-hidden rounded-2xl border-2 border-dashed border-border h-full min-h-[200px]">
                <div className="h-full flex flex-col items-center justify-center p-6 text-center gap-3 aspect-[3/4]">
                  <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                    <ImageIcon className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <p className="text-sm font-semibold text-muted-foreground">
                    +{preview.totalPages - preview.previewPages.length} more pages
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Unlock the full book to access all {preview.totalPages} coloring pages
                  </p>
                </div>
              </Card>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="rounded-3xl shadow-xl border-2 border-[#6B21A8]/10 bg-gradient-to-br from-white to-amber-50/40">
              <CardContent className="p-8">
                <div className="text-center mb-8">
                  <h2 className="text-2xl md:text-3xl font-bold mb-2">
                    Get Your Complete Coloring Book
                  </h2>
                  <p className="text-muted-foreground">
                    All {preview.totalPages} personalised pages, ready to color — your way
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
                      {['Instant access after purchase', 'Print at home or at a print shop', 'All pages in high resolution'].map((item) => (
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
                      <h3 className="font-bold text-base">Printed & Delivered</h3>
                      <p className="text-sm text-muted-foreground mt-0.5">
                        A professionally printed and bound coloring book shipped to your door
                      </p>
                    </div>
                    <ul className="space-y-1.5 mt-auto">
                      {['Premium soft or hardcover binding', 'Professional print quality', 'Ships in 5–7 business days'].map((item) => (
                        <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                          <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Link href={`/checkout/${bookId}?format=digital`} className="flex-1 sm:flex-none">
                    <Button
                      size="lg"
                      className="w-full sm:w-auto rounded-2xl px-8 py-6 text-base bg-[#6B21A8] hover:bg-[#581C87] gap-2"
                    >
                      <Download className="h-5 w-5" />
                      Download PDF
                    </Button>
                  </Link>
                  <Link href={`/checkout/${bookId}?format=print`} className="flex-1 sm:flex-none">
                    <Button
                      size="lg"
                      variant="outline"
                      className="w-full sm:w-auto rounded-2xl px-8 py-6 text-base border-2 border-[#C9A227] text-[#C9A227] hover:bg-amber-50 gap-2"
                    >
                      <Printer className="h-5 w-5" />
                      Order Print Copy
                    </Button>
                  </Link>
                </div>

                <p className="text-center text-xs text-muted-foreground mt-5">
                  <Sparkles className="inline h-3.5 w-3.5 mr-1 text-[#C9A227]" />
                  Every page features your child as the star of the story
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      </main>

      <footer className="relative z-10 border-t mt-16 py-8 bg-white/60 backdrop-blur">
        <div className="container mx-auto px-4 text-center text-muted-foreground text-sm">
          &copy; 2026 Pandora Pages. Crafted for you, one page at a time.
        </div>
      </footer>
    </div>
  );
}
