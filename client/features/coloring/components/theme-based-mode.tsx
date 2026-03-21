'use client';

import { useState } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { ImagePlus, X, Sparkles, Loader, Check, BookOpen, User, CircleAlert as AlertCircle, Star, Camera, Mail, Hash } from 'lucide-react';
import { toast } from 'sonner';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { ThemeBasedSubmitData, PublicTheme } from '@/types/book.types';
import { useActiveThemes } from '@/features/coloring/hooks/useColoringTemplates';
import { useColoringContext } from '@/features/coloring/context/coloring-context';

const MIN_PHOTOS = 1;
const MAX_PHOTOS = 5;
const MIN_PAGES = 8;
const MAX_PAGES = 32;

const FALLBACK_COVER =
  'https://images.pexels.com/photos/3094220/pexels-photo-3094220.jpeg?auto=compress&cs=tinysrgb&w=300';

const PAGE_TIER_LABELS: Record<number, { label: string; emoji: string }> = {
  8:  { label: 'Mini Book',   emoji: '📖' },
  12: { label: 'Small Book',  emoji: '📗' },
  16: { label: 'Classic',     emoji: '📘' },
  20: { label: 'Adventure',   emoji: '📙' },
  24: { label: 'Deluxe',      emoji: '📚' },
  28: { label: 'Epic',        emoji: '🌟' },
  32: { label: 'Mega Book',   emoji: '👑' },
};

const schema = z.object({
  childName: z.string().min(1, 'Child name is required').max(50),
  age: z.number({ invalid_type_error: 'Age is required' }).min(1).max(12),
  parentEmail: z.string().email('Invalid email address'),
});

type FormData = z.infer<typeof schema>;

type Props = {
  onSubmit: (data: ThemeBasedSubmitData) => void;
  isPending: boolean;
};

function SectionHeader({
  step,
  title,
  subtitle,
  accentColor = 'purple',
}: {
  step: number;
  title: string;
  subtitle: string;
  accentColor?: 'purple' | 'amber' | 'pink';
}) {
  const accent = {
    purple: { badge: 'bg-purple-100 text-purple-700', dot: 'bg-[#6B21A8]' },
    amber:  { badge: 'bg-amber-100  text-amber-700',  dot: 'bg-amber-500'  },
    pink:   { badge: 'bg-pink-100   text-pink-700',   dot: 'bg-pink-500'   },
  }[accentColor];

  return (
    <div className="flex items-start gap-4 mb-6">
      <div className={`w-9 h-9 rounded-2xl ${accent.dot} flex items-center justify-center flex-shrink-0 shadow-sm`}>
        <span className="text-white text-sm font-bold">{step}</span>
      </div>
      <div>
        <h2 className="text-lg font-bold leading-tight">{title}</h2>
        <p className="text-sm text-muted-foreground mt-0.5">{subtitle}</p>
      </div>
    </div>
  );
}

export function ThemeBasedMode({ onSubmit, isPending }: Props) {
  const { data: themes = [], isLoading: isThemesLoading, isError: isThemesError } = useActiveThemes();
  const { state, dispatch } = useColoringContext();

  const selectedTheme = state.selectedTheme;
  const pageCount = state.pageCount;

  const [photos, setPhotos] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [photoError, setPhotoError] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { age: state.formData.childAge },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const remaining = MAX_PHOTOS - photos.length;
    if (remaining <= 0) {
      toast.error(`Maximum ${MAX_PHOTOS} photos allowed`);
      return;
    }
    const toAdd = files.slice(0, remaining);
    const newPreviews = toAdd.map((f) => URL.createObjectURL(f));
    setPhotos((prev) => [...prev, ...toAdd]);
    setPreviews((prev) => [...prev, ...newPreviews]);
    setPhotoError(false);
    e.target.value = '';
  };

  const removePhoto = (index: number) => {
    URL.revokeObjectURL(previews[index]);
    setPhotos((prev) => prev.filter((_, i) => i !== index));
    setPreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSelectTheme = (theme: PublicTheme) => {
    dispatch({ type: 'SET_THEME', payload: theme });
  };

  const handlePageCountChange = (value: number) => {
    dispatch({ type: 'SET_PAGE_COUNT', payload: value });
  };

  const onFormSubmit = (data: FormData) => {
    if (!selectedTheme) {
      toast.error('Please select a theme');
      return;
    }
    if (photos.length < MIN_PHOTOS) {
      setPhotoError(true);
      toast.error('Please upload at least one photo of your child');
      return;
    }
    dispatch({
      type: 'SET_FORM_DATA',
      payload: { childName: data.childName, childAge: data.age, parentEmail: data.parentEmail },
    });
    onSubmit({
      themeConfigId: selectedTheme.id,
      numPages: pageCount,
      coloringStyle: 'simple',
      childName: data.childName,
      childAge: data.age,
      parentEmail: data.parentEmail,
      photos,
    });
  };

  const pageTier = PAGE_TIER_LABELS[pageCount] ?? { label: `${pageCount} pages`, emoji: '📄' };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-2">

      {/* ── Step 1: Theme Selection ── */}
      <div className="rounded-3xl border border-purple-100 bg-white/70 backdrop-blur-sm p-6 shadow-sm">
        <SectionHeader
          step={1}
          title="Pick a Magical Theme ✨"
          subtitle={`Our AI crafts ${pageCount} unique scenes based on the world you choose — your child stars in every one!`}
          accentColor="purple"
        />

        {isThemesError && (
          <div className="flex items-center gap-2 text-destructive text-sm mb-4 bg-red-50 rounded-2xl px-4 py-3">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            Failed to load themes. Please refresh the page.
          </div>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {isThemesLoading
            ? Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="rounded-2xl border-2 border-purple-100 overflow-hidden animate-pulse">
                  <div className="h-28 w-full bg-purple-50" />
                  <div className="p-3 space-y-2">
                    <div className="h-3 bg-purple-100 rounded-full w-3/4" />
                    <div className="h-2.5 bg-purple-50 rounded-full w-full" />
                  </div>
                </div>
              ))
            : themes.map((theme) => {
                const isSelected = selectedTheme?.id === theme.id;
                const coverSrc = theme.previewImageUrl ?? FALLBACK_COVER;
                return (
                  <button
                    key={theme.id}
                    type="button"
                    onClick={() => handleSelectTheme(theme)}
                    className={`relative text-left rounded-2xl overflow-hidden transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#6B21A8] focus-visible:ring-offset-2 ${
                      isSelected
                        ? 'ring-2 ring-[#6B21A8] ring-offset-2 shadow-lg shadow-purple-100 scale-[1.02]'
                        : 'border border-purple-100 hover:border-purple-300 hover:shadow-md hover:scale-[1.01] hover:shadow-purple-50'
                    }`}
                  >
                    {/* Image */}
                    <div className="relative h-28 w-full">
                      <Image
                        src={coverSrc}
                        alt={theme.displayName}
                        fill
                        className="object-cover"
                      />
                      <div
                        className={`absolute inset-0 transition-opacity ${
                          isSelected
                            ? 'bg-gradient-to-t from-[#6B21A8]/60 via-[#6B21A8]/10 to-transparent'
                            : 'bg-gradient-to-t from-black/40 via-transparent to-transparent'
                        }`}
                      />
                      {isSelected && (
                        <div className="absolute top-2 right-2 bg-[#6B21A8] rounded-full w-6 h-6 flex items-center justify-center shadow-md">
                          <Check className="h-3.5 w-3.5 text-white" />
                        </div>
                      )}
                      {theme.isPremium && (
                        <div className="absolute top-2 left-2 bg-amber-400 rounded-full px-2 py-0.5 flex items-center gap-0.5 shadow-sm">
                          <Star className="h-2.5 w-2.5 text-white fill-white" />
                          <span className="text-[9px] font-bold text-white uppercase tracking-wide">Premium</span>
                        </div>
                      )}
                    </div>

                    {/* Label */}
                    <div className={`p-2.5 ${isSelected ? 'bg-purple-50' : 'bg-white'}`}>
                      <span className="text-xs font-semibold leading-tight block">{theme.displayName}</span>
                      {theme.description && (
                        <p className="text-[10px] text-muted-foreground leading-tight line-clamp-2 mt-0.5">
                          {theme.description}
                        </p>
                      )}
                    </div>
                  </button>
                );
              })}
        </div>

        {/* Selected theme pill */}
        {selectedTheme && (
          <div className="mt-4 inline-flex items-center gap-2 bg-purple-50 border border-purple-200 rounded-full px-4 py-1.5">
            <div className="w-2 h-2 rounded-full bg-[#6B21A8]" />
            <span className="text-sm font-semibold text-[#6B21A8]">{selectedTheme.displayName}</span>
            <span className="text-xs text-purple-400">selected</span>
          </div>
        )}
      </div>

      {/* ── Step 2: Photos ── */}
      <div className="rounded-3xl border border-amber-100 bg-white/70 backdrop-blur-sm p-6 shadow-sm">
        <SectionHeader
          step={2}
          title="Add Your Child's Photos 📸"
          subtitle="We'll place your child as the star of every coloring page. Front-facing, well-lit photos work best."
          accentColor="amber"
        />

        <div className={`rounded-2xl border-2 transition-colors ${photoError ? 'border-red-200 bg-red-50/40' : 'border-amber-100 bg-amber-50/30'}`}>
          <div className="p-5">
            {/* Upload zone */}
            {photos.length < MAX_PHOTOS && (
              <label
                htmlFor="theme-photo-input"
                className="group flex flex-col items-center justify-center gap-3 border-2 border-dashed border-amber-200 rounded-2xl p-6 cursor-pointer hover:border-amber-400 hover:bg-amber-50/60 transition-all"
              >
                <div className="w-14 h-14 rounded-2xl bg-amber-100 group-hover:bg-amber-200 flex items-center justify-center transition-colors">
                  <Camera className="h-7 w-7 text-amber-500" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-foreground">
                    Drop photos here or <span className="text-amber-600 underline underline-offset-2">browse</span>
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {photos.length}/{MAX_PHOTOS} photos added · JPG, PNG, WEBP
                  </p>
                </div>
                <input
                  id="theme-photo-input"
                  type="file"
                  accept="image/*"
                  multiple
                  className="hidden"
                  onChange={handleFileChange}
                />
              </label>
            )}

            {/* Photo previews */}
            {previews.length > 0 && (
              <div className={`grid grid-cols-5 gap-3 ${photos.length < MAX_PHOTOS ? 'mt-4' : ''}`}>
                {previews.map((src, i) => (
                  <div key={i} className="relative aspect-square rounded-xl overflow-hidden group ring-2 ring-amber-100">
                    <Image src={src} alt={`Photo ${i + 1}`} fill className="object-cover" />
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors rounded-xl" />
                    <button
                      type="button"
                      onClick={() => removePhoto(i)}
                      className="absolute top-1 right-1 bg-white text-destructive rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-md"
                    >
                      <X className="h-3 w-3" />
                    </button>
                    <div className="absolute bottom-1 left-1 bg-black/50 text-white text-[9px] font-bold rounded-full px-1.5 py-0.5">
                      {i + 1}
                    </div>
                  </div>
                ))}
                {/* Add more slot */}
                {photos.length < MAX_PHOTOS && (
                  <label
                    htmlFor="theme-photo-input"
                    className="relative aspect-square rounded-xl border-2 border-dashed border-amber-200 flex items-center justify-center cursor-pointer hover:border-amber-400 hover:bg-amber-50 transition-all"
                  >
                    <ImagePlus className="h-6 w-6 text-amber-400" />
                  </label>
                )}
              </div>
            )}

            {photoError && photos.length === 0 && (
              <div className="flex items-center gap-2 mt-3 text-red-500 text-sm bg-red-50 rounded-xl px-3 py-2">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                At least one photo is required to personalise your book
              </div>
            )}

            {/* Tips */}
            <div className="mt-4 flex flex-wrap gap-2">
              {['Clear, front-facing face', 'Good lighting', 'No hats or sunglasses'].map((tip) => (
                <span key={tip} className="inline-flex items-center gap-1 text-[11px] text-amber-700 bg-amber-50 border border-amber-100 rounded-full px-2.5 py-1">
                  <Check className="h-2.5 w-2.5" />
                  {tip}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Step 3: Book Details ── */}
      <div className="rounded-3xl border border-pink-100 bg-white/70 backdrop-blur-sm p-6 shadow-sm">
        <SectionHeader
          step={3}
          title="Tell Us About Your Child 🎉"
          subtitle="These details help us personalise the book just for them."
          accentColor="pink"
        />

        <div className="grid md:grid-cols-2 gap-6">
          {/* Left: name, age, email */}
          <div className="space-y-4">
            {/* Child name */}
            <div>
              <Label htmlFor="childName-theme" className="flex items-center gap-1.5 text-sm font-semibold mb-1.5">
                <User className="h-3.5 w-3.5 text-pink-500" />
                Child&apos;s Name <span className="text-red-400">*</span>
              </Label>
              <Input
                id="childName-theme"
                {...register('childName')}
                placeholder="e.g. Lily, Max, Amara…"
                className="rounded-xl border-pink-100 focus:border-pink-300 focus-visible:ring-pink-200"
              />
              {errors.childName && (
                <p className="text-xs text-destructive mt-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> {errors.childName.message}
                </p>
              )}
            </div>

            {/* Age */}
            <div>
              <Label htmlFor="age-theme" className="flex items-center gap-1.5 text-sm font-semibold mb-1.5">
                <Hash className="h-3.5 w-3.5 text-pink-500" />
                Age <span className="text-red-400">*</span>
              </Label>
              <Input
                id="age-theme"
                type="number"
                min={1}
                max={12}
                {...register('age', { valueAsNumber: true })}
                placeholder="e.g. 5"
                className="rounded-xl border-pink-100 focus:border-pink-300 focus-visible:ring-pink-200"
              />
              {errors.age && (
                <p className="text-xs text-destructive mt-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> {errors.age.message}
                </p>
              )}
            </div>

            {/* Email */}
            <div>
              <Label htmlFor="parentEmail-theme" className="flex items-center gap-1.5 text-sm font-semibold mb-1.5">
                <Mail className="h-3.5 w-3.5 text-pink-500" />
                Parent Email <span className="text-red-400">*</span>
              </Label>
              <Input
                id="parentEmail-theme"
                type="email"
                {...register('parentEmail')}
                placeholder="parent@example.com"
                className="rounded-xl border-pink-100 focus:border-pink-300 focus-visible:ring-pink-200"
              />
              {errors.parentEmail && (
                <p className="text-xs text-destructive mt-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> {errors.parentEmail.message}
                </p>
              )}
            </div>
          </div>

          {/* Right: page count */}
          <div>
            <Label className="flex items-center gap-1.5 text-sm font-semibold mb-3">
              <BookOpen className="h-3.5 w-3.5 text-pink-500" />
              Number of Pages
            </Label>

            {/* Page tier badge */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 bg-purple-50 border border-purple-200 rounded-2xl px-4 py-2">
                <span className="text-xl">{pageTier.emoji}</span>
                <div>
                  <p className="text-xs text-purple-500 font-medium">{pageTier.label}</p>
                  <p className="text-lg font-bold text-[#6B21A8] leading-none">{pageCount} pages</p>
                </div>
              </div>
              <p className="text-xs text-muted-foreground text-right max-w-[120px]">
                Each page features your child in a unique scene
              </p>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-muted-foreground w-6 text-center">{MIN_PAGES}</span>
              <Slider
                min={MIN_PAGES}
                max={MAX_PAGES}
                step={4}
                value={[pageCount]}
                onValueChange={([v]) => handlePageCountChange(v)}
                className="flex-1"
              />
              <span className="text-xs font-semibold text-muted-foreground w-6 text-center">{MAX_PAGES}</span>
            </div>

            {/* Page count ticks */}
            <div className="flex justify-between mt-1.5 px-4">
              {Array.from({ length: (MAX_PAGES - MIN_PAGES) / 4 + 1 }, (_, i) => MIN_PAGES + i * 4).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => handlePageCountChange(p)}
                  className={`text-[10px] font-medium transition-colors ${
                    p === pageCount ? 'text-[#6B21A8] font-bold' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Book summary preview ── */}
      {selectedTheme && photos.length > 0 && (
        <div className="rounded-3xl overflow-hidden border border-purple-200 shadow-sm">
          <div className="bg-gradient-to-r from-[#6B21A8] to-violet-600 px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-white/20 flex items-center justify-center">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div>
                <p className="text-white/70 text-xs font-medium uppercase tracking-wider">Your book is ready to create</p>
                <p className="text-white font-bold text-base leading-tight mt-0.5">
                  {pageTier.emoji}&nbsp;
                  <span className="text-yellow-300">{pageCount}-page</span> &quot;{selectedTheme.displayName}&quot; adventure
                </p>
              </div>
            </div>
          </div>
          <div className="bg-purple-50/80 px-6 py-3 flex items-center gap-6 flex-wrap">
            <div className="flex items-center gap-1.5 text-xs text-purple-700">
              <Check className="h-3.5 w-3.5 text-green-500" />
              Theme selected
            </div>
            <div className="flex items-center gap-1.5 text-xs text-purple-700">
              <Check className="h-3.5 w-3.5 text-green-500" />
              {photos.length} photo{photos.length > 1 ? 's' : ''} uploaded
            </div>
            <div className="flex items-center gap-1.5 text-xs text-purple-700">
              <Check className="h-3.5 w-3.5 text-green-500" />
              AI personalisation enabled
            </div>
          </div>
        </div>
      )}

      {/* ── Submit ── */}
      <Button
        type="submit"
        disabled={isPending || !selectedTheme || isThemesLoading}
        className="w-full rounded-2xl text-base font-bold py-7 bg-gradient-to-r from-[#6B21A8] to-violet-600 hover:from-[#581C87] hover:to-violet-700 shadow-lg shadow-purple-200 transition-all hover:shadow-purple-300 hover:scale-[1.01] disabled:opacity-60 disabled:scale-100 disabled:shadow-none"
      >
        {isPending ? (
          <span className="flex items-center gap-3">
            <Loader className="h-5 w-5 animate-spin" />
            Crafting your personalised book…
          </span>
        ) : (
          <span className="flex items-center gap-3">
            <Sparkles className="h-5 w-5" />
            Create My Personalised Coloring Book
            <span className="ml-auto text-white/60 text-sm font-normal hidden sm:inline">
              ✨ 100% unique
            </span>
          </span>
        )}
      </Button>
    </form>
  );
}
