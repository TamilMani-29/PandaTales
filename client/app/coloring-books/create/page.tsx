'use client';

import React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PhotoUploadMode } from '@/features/coloring/components/photo-upload-mode';
import { ThemeBasedMode } from '@/features/coloring/components/theme-based-mode';
import { Footer } from '@/components/layout/footer';
import {
  ColoringBookMode,
  ThemeBasedSubmitData,
  PhotoColoringSubmitData,
} from '@/types/book.types';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, Palette, ArrowLeft, Sparkles, Check, BookOpen } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import { cn } from '@/lib/utils';
import {
  ColoringProvider,
  useColoringContext,
} from '@/features/coloring/context/coloring-context';
import { coloringTemplatesService } from '@/features/coloring/services/coloring-templates.service';

const FALLBACK_COVER =
  'https://images.pexels.com/photos/3094220/pexels-photo-3094220.jpeg?auto=compress&cs=tinysrgb&w=300';

const modeOptions: {
  id: ColoringBookMode;
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  description: string;
  badge: string;
  badgeColor: string;
  borderColor: string;
}[] = [
  {
    id: 'photo',
    icon: <Camera className="h-8 w-8" />,
    title: 'Photo to Coloring Pages',
    subtitle: 'Upload photos, get coloring pages',
    description:
      'Upload up to 10 photos and we convert each one into a beautiful hand-drawn style coloring page. Perfect for family photos, pets, or any special memories.',
    badge: 'Up to 10 pages',
    badgeColor: 'bg-violet-100 text-violet-700',
    borderColor: 'border-violet-200 hover:border-violet-400',
  },
  {
    id: 'theme',
    icon: <Palette className="h-8 w-8" />,
    title: 'Theme-Based Coloring Book',
    subtitle: 'Pick a theme, we create the book',
    description:
      "Choose from magical themes — Space, Jungle, Princess and more. We generate a complete coloring book with defined scenes. Optionally add your child's photos to personalise each illustration.",
    badge: '8–32 pages',
    badgeColor: 'bg-amber-100 text-amber-700',
    borderColor: 'border-amber-200 hover:border-amber-400',
  },
];

const STEPS = [
  { n: 1, label: 'Pick a Theme',     hint: 'Choose the adventure world',   accent: 'bg-[#6B21A8]' },
  { n: 2, label: 'Add Photos',        hint: 'Your child stars in every page', accent: 'bg-amber-500' },
  { n: 3, label: 'About Your Child',  hint: 'Name, age & delivery details',  accent: 'bg-pink-500'  },
];

// ── Inner component – has access to ColoringContext ────────────────────────────────────────────
function CreateColoringBookContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { state, dispatch } = useColoringContext();

  const modeParam = searchParams.get('mode') as ColoringBookMode | null;
  const selectedMode =
    state.mode ?? (modeParam === 'photo' || modeParam === 'theme' ? modeParam : null);

  const handleSelectMode = (mode: ColoringBookMode) => {
    dispatch({ type: 'SET_MODE', payload: mode });
  };

  // ── Theme-based generation mutation ──────────────────────────────────────────────────
  const { mutate: submitThemeBased, isPending: isThemePending } = useMutation({
    mutationFn: (data: ThemeBasedSubmitData) =>
      coloringTemplatesService.generateThemeBased(data),
    onSuccess: (result) => {
      toast.success('Your coloring book is being crafted!');
      dispatch({ type: 'RESET' });
      router.push(`/preview/${result.id}`);
    },
    onError: () => {
      toast.error('Something went wrong. Please try again.');
    },
  });

  // ── Photo-to-coloring generation mutation ─────────────────────────────────────────────────
  const { mutate: submitPhotoColoring, isPending: isPhotoPending } = useMutation({
    mutationFn: (data: PhotoColoringSubmitData) =>
      coloringTemplatesService.generatePhotoColoring(data),
    onSuccess: (result) => {
      toast.success('Your coloring book is being crafted!');
      dispatch({ type: 'RESET' });
      router.push(`/preview/${result.id}`);
    },
    onError: () => {
      toast.error('Something went wrong. Please try again.');
    },
  });

  const isPending = isThemePending || isPhotoPending;
  const selectedTheme = state.selectedTheme;
  const pageCount = state.pageCount;
  const childName = state.formData?.childName;

  return (
    <div className="min-h-screen relative">
      <main className="relative z-10 container mx-auto px-4 py-6 md:py-8">
        {/* ── Page header – left-aligned like story books ── */}
        <div className="mb-6 md:mb-8">
          <div className="flex items-center gap-2 mb-3">
            {!selectedMode ? (
              <Link href="/coloring-books">
                <Button
                  variant="ghost"
                  size="sm"
                  className="rounded-xl gap-1.5 text-muted-foreground hover:text-foreground -ml-2"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </Button>
              </Link>
            ) : (
              <button
                onClick={() => dispatch({ type: 'SET_MODE', payload: null })}
                className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors -ml-1"
              >
                <ArrowLeft className="h-4 w-4" />
                Choose a different method
              </button>
            )}
          </div>
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-3 bg-gradient-to-r from-[#6B21A8] to-[#C9A227] bg-clip-text text-transparent">
            Create Your Coloring Book
          </h1>
          {selectedMode ? (
            <Badge
              variant="outline"
              className={cn(
                'rounded-full text-xs font-semibold',
                selectedMode === 'photo'
                  ? 'border-violet-200 text-violet-700 bg-violet-50'
                  : 'border-amber-200 text-amber-700 bg-amber-50'
              )}
            >
              {selectedMode === 'photo' ? 'Photo to Coloring Pages' : 'Theme-Based Book'}
            </Badge>
          ) : (
            <p className="text-base md:text-lg text-muted-foreground">
              Choose how you&apos;d like to create your personalised coloring book
            </p>
          )}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          {!selectedMode ? (
            /* ── Mode selection cards ── */
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid md:grid-cols-2 gap-6 max-w-3xl"
            >
              {modeOptions.map((option, i) => (
                <motion.div
                  key={option.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <button
                    className={`w-full text-left rounded-3xl border-2 p-8 transition-all shadow-md hover:shadow-xl ${option.borderColor} bg-white`}
                    onClick={() => handleSelectMode(option.id)}
                  >
                    <div
                      className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-5 text-[#6B21A8] ${
                        option.id === 'photo' ? 'bg-violet-100' : 'bg-amber-50'
                      }`}
                    >
                      {option.icon}
                    </div>
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <h2 className="text-2xl font-bold">{option.title}</h2>
                      <span
                        className={`text-xs font-semibold px-3 py-1 rounded-full flex-shrink-0 mt-1 ${option.badgeColor}`}
                      >
                        {option.badge}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-[#6B21A8] mb-3">{option.subtitle}</p>
                    <p className="text-muted-foreground text-sm leading-relaxed">
                      {option.description}
                    </p>
                    <div className="mt-6">
                      <span className="inline-flex items-center gap-2 text-sm font-semibold text-[#6B21A8]">
                        <Sparkles className="h-4 w-4" />
                        Get started
                      </span>
                    </div>
                  </button>
                </motion.div>
              ))}
            </motion.div>
          ) : (
            <AnimatePresence mode="wait">
              <motion.div
                key={selectedMode}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                transition={{ duration: 0.3 }}
              >
                {/* ── Sidebar + Form grid – mirrors story books layout ── */}
                <div className="grid lg:grid-cols-[260px_1fr] gap-8">

                  {/* Desktop sidebar */}
                  <aside className="hidden lg:block">
                    <div className="sticky top-20 space-y-3">

                      {/* Steps progress */}
                      <div className="rounded-2xl border bg-card p-4 space-y-1">
                        <p className="text-xs font-semibold text-foreground/60 uppercase tracking-wide mb-3">Your Steps</p>
                        {STEPS.map((step, idx) => {
                          const done =
                            (idx === 0 && !!selectedTheme) ||
                            (idx === 2 && !!childName);
                          return (
                            <div key={step.n} className="flex items-start gap-3 py-2">
                              <div
                                className={cn(
                                  'w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5',
                                  done
                                    ? 'bg-green-500 text-white'
                                    : `${step.accent} text-white opacity-60`
                                )}
                              >
                                {done ? <Check className="h-3 w-3" /> : step.n}
                              </div>
                              <div>
                                <p className={cn('text-sm font-medium leading-tight', done ? 'text-foreground' : 'text-muted-foreground')}>
                                  {step.label}
                                </p>
                                <p className="text-xs text-muted-foreground mt-0.5">{step.hint}</p>
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Selected theme preview */}
                      {selectedTheme ? (
                        <div className="rounded-2xl border bg-card overflow-hidden">
                          <div className="relative h-36">
                            <Image
                              src={selectedTheme.previewImageUrl ?? FALLBACK_COVER}
                              alt={selectedTheme.displayName}
                              fill
                              className="object-cover"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                            <div className="absolute bottom-2.5 left-3 right-3">
                              <p className="text-white font-semibold text-sm leading-tight">{selectedTheme.displayName}</p>
                            </div>
                          </div>
                          <div className="p-3 flex items-center gap-2">
                            <BookOpen className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                            <span className="text-sm font-medium text-[#6B21A8]">{pageCount} pages</span>
                            <span className="text-xs text-muted-foreground ml-auto">selected</span>
                          </div>
                        </div>
                      ) : (
                        <div className="rounded-2xl border bg-card p-5 text-center space-y-2">
                          <div className="w-10 h-10 rounded-2xl bg-purple-50 flex items-center justify-center mx-auto">
                            <Palette className="h-5 w-5 text-purple-400" />
                          </div>
                          <p className="text-sm text-muted-foreground">No theme selected yet</p>
                          <p className="text-xs text-muted-foreground/60">Pick one from Step 1</p>
                        </div>
                      )}

                      {/* Page count pill */}
                      <div className="rounded-2xl border bg-card px-4 py-3 flex items-center justify-between">
                        <span className="text-xs text-muted-foreground font-medium">Book size</span>
                        <span className="text-sm font-bold text-[#6B21A8] bg-purple-50 px-3 py-1 rounded-full">
                          {pageCount} pages
                        </span>
                      </div>

                    </div>
                  </aside>

                  {/* Main form content */}
                  <div>
                    {selectedMode === 'photo' ? (
                      <Card className="rounded-3xl shadow-lg">
                        <CardContent className="p-6 md:p-8">
                          <PhotoUploadMode onSubmit={submitPhotoColoring} isPending={isPending} />
                        </CardContent>
                      </Card>
                    ) : (
                      <ThemeBasedMode onSubmit={submitThemeBased} isPending={isPending} />
                    )}
                  </div>

                </div>
              </motion.div>
            </AnimatePresence>
          )}
        </motion.div>
      </main>

      <Footer />
    </div>
  );
}

// ── Page – wraps content with ColoringProvider ────────────────────────────────────────────
export default function CreateColoringBookPage() {
  return (
    <ColoringProvider>
      <CreateColoringBookContent />
    </ColoringProvider>
  );
}

