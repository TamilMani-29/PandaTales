'use client';

import React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PhotoUploadMode } from '@/features/coloring/components/photo-upload-mode';
import { ThemeBasedMode } from '@/features/coloring/components/theme-based-mode';
import {
  ColoringBookMode,
  ThemeBasedSubmitData,
  PhotoColoringSubmitData,
} from '@/types/book.types';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, Palette, ArrowLeft, Sparkles } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import {
  ColoringProvider,
  useColoringContext,
} from '@/features/coloring/context/coloring-context';
import { coloringTemplatesService } from '@/features/coloring/services/coloring-templates.service';

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

// ── Inner component – has access to ColoringContext ───────────────────────────
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

  // ── Theme-based generation mutation ──────────────────────────────────────
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

  // ── Photo-to-coloring generation mutation ─────────────────────────────────
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

  return (
    <div className="min-h-screen relative">
      <main className="relative z-10 container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="max-w-5xl mx-auto"
        >
          {!selectedMode && (
            <div className="flex items-center gap-3 mb-2">
              <Link href="/coloring-books">
                <Button
                  variant="ghost"
                  size="sm"
                  className="rounded-xl gap-1.5 text-muted-foreground hover:text-foreground"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </Button>
              </Link>
            </div>
          )}

          <div className="text-center mb-10">
            <div className="flex justify-center mb-4">
              <Image
                src="/logo_without_name.jpeg"
                alt="Pandora Pages"
                width={56}
                height={56}
                className="object-contain"
              />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-3 bg-gradient-to-r from-[#6B21A8] to-[#C9A227] bg-clip-text text-transparent">
              Create Your Coloring Book
            </h1>
            <p className="text-lg text-muted-foreground max-w-xl mx-auto">
              Choose how you&apos;d like to create your personalized coloring book
            </p>
          </div>

          {!selectedMode ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid md:grid-cols-2 gap-6"
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
                <div className="flex items-center gap-3 mb-6">
                  <button
                    onClick={() => dispatch({ type: 'SET_MODE', payload: null })}
                    className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    Choose a different method
                  </button>
                  <div className="h-4 w-px bg-border" />
                  <span
                    className={`text-xs font-semibold px-3 py-1 rounded-full ${
                      selectedMode === 'photo'
                        ? 'bg-violet-100 text-violet-700'
                        : 'bg-amber-100 text-amber-700'
                    }`}
                  >
                    {selectedMode === 'photo' ? 'Photo to Coloring Pages' : 'Theme-Based Book'}
                  </span>
                </div>

                {selectedMode === 'photo' ? (
                  <Card className="rounded-3xl shadow-lg">
                    <CardContent className="p-8">
                      <PhotoUploadMode onSubmit={submitPhotoColoring} isPending={isPending} />
                    </CardContent>
                  </Card>
                ) : (
                  <ThemeBasedMode onSubmit={submitThemeBased} isPending={isPending} />
                )}
              </motion.div>
            </AnimatePresence>
          )}
        </motion.div>
      </main>

      <footer className="relative z-10 border-t mt-20 py-8 bg-white/60 backdrop-blur">
        <div className="container mx-auto px-4 text-center text-muted-foreground">
          <p>&copy; 2026 Pandora Pages. Crafted for you, one page at a time.</p>
        </div>
      </footer>
    </div>
  );
}

// ── Page – wraps content with ColoringProvider ────────────────────────────────
export default function CreateColoringBookPage() {
  return (
    <ColoringProvider>
      <CreateColoringBookContent />
    </ColoringProvider>
  );
}
