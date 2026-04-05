'use client';

import { useState } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { ImagePlus, X, Sparkles, Loader, Check, Star, Camera, Mail, AlertCircle as AlertCircleIcon } from 'lucide-react';
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
  8:  { label: 'Mini',      emoji: 'ðŸ“–' },
  12: { label: 'Small',     emoji: 'ðŸ“—' },
  16: { label: 'Classic',   emoji: 'ðŸ“˜' },
  20: { label: 'Adventure', emoji: 'ðŸ“™' },
  24: { label: 'Deluxe',    emoji: 'ðŸ“š' },
  28: { label: 'Epic',      emoji: 'ðŸŒŸ' },
  32: { label: 'Mega',      emoji: 'ðŸ‘‘' },
};

const schema = z.object({
  childName: z.string().min(1, 'Child name is required').max(50),
  age: z.number({ invalid_type_error: 'Age is required' }).min(1).max(12),
  parentEmail: z.string().email('Invalid email address'),
  whatsappNumber: z.string().regex(/^[0-9+\s\-]{7,20}$/, 'Enter a valid WhatsApp number').optional().or(z.literal('')),
});

type FormData = z.infer<typeof schema>;

type Props = {
  onSubmit: (data: ThemeBasedSubmitData) => void;
  isPending: boolean;
};

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
    if (remaining <= 0) { toast.error(`Maximum ${MAX_PHOTOS} photos allowed`); return; }
    const toAdd = files.slice(0, remaining);
    setPhotos((prev) => [...prev, ...toAdd]);
    setPreviews((prev) => [...prev, ...toAdd.map((f) => URL.createObjectURL(f))]);
    setPhotoError(false);
    e.target.value = '';
  };

  const removePhoto = (index: number) => {
    URL.revokeObjectURL(previews[index]);
    setPhotos((prev) => prev.filter((_, i) => i !== index));
    setPreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const onFormSubmit = (data: FormData) => {
    if (!selectedTheme) { toast.error('Please select a theme'); return; }
    if (photos.length < MIN_PHOTOS) {
      setPhotoError(true);
      toast.error('Please upload at least one photo of your child');
      return;
    }
    dispatch({ type: 'SET_FORM_DATA', payload: { childName: data.childName, childAge: data.age, parentEmail: data.parentEmail } });
    onSubmit({
      themeConfigId: selectedTheme.id,
      numPages: pageCount,
      coloringStyle: 'simple',
      childName: data.childName,
      childAge: data.age,
      parentEmail: data.parentEmail,
      whatsappNumber: data.whatsappNumber || undefined,
      photos,
    });
  };

  const pageTier = PAGE_TIER_LABELS[pageCount] ?? { label: `${pageCount}`, emoji: 'ðŸ“„' };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-8">

      {/* â”€â”€ Step 1: Theme â”€â”€ */}
      <div className="space-y-3">
        <div>
          <p className="text-sm font-semibold text-foreground">Choose a Theme *</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Our AI crafts unique illustrated scenes based on the world you pick
          </p>
        </div>

        {isThemesError && (
          <div className="flex items-center gap-2 text-destructive text-sm bg-red-50 rounded-xl px-3 py-2.5">
            <AlertCircleIcon className="h-4 w-4 flex-shrink-0" />
            Failed to load themes. Please refresh the page.
          </div>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {isThemesLoading
            ? Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="rounded-xl border overflow-hidden animate-pulse">
                  <div className="h-24 w-full bg-muted" />
                  <div className="p-2.5 space-y-1.5">
                    <div className="h-2.5 bg-muted rounded-full w-3/4" />
                    <div className="h-2 bg-muted/60 rounded-full w-full" />
                  </div>
                </div>
              ))
            : themes.map((theme) => {
                const isSelected = selectedTheme?.id === theme.id;
                return (
                  <button
                    key={theme.id}
                    type="button"
                    onClick={() => dispatch({ type: 'SET_THEME', payload: theme })}
                    className={`relative text-left rounded-xl overflow-hidden transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#6B21A8] focus-visible:ring-offset-1 ${
                      isSelected
                        ? 'ring-2 ring-[#6B21A8] ring-offset-1 shadow-md'
                        : 'border hover:border-[#6B21A8]/40 hover:shadow-sm'
                    }`}
                  >
                    <div className="relative h-24 w-full">
                      <Image
                        src={theme.previewImageUrl ?? FALLBACK_COVER}
                        alt={theme.displayName}
                        fill
                        className="object-cover"
                      />
                      <div className={`absolute inset-0 ${isSelected ? 'bg-gradient-to-t from-[#6B21A8]/50 to-transparent' : 'bg-gradient-to-t from-black/30 to-transparent'}`} />
                      {isSelected && (
                        <div className="absolute top-1.5 right-1.5 bg-[#6B21A8] rounded-full w-5 h-5 flex items-center justify-center shadow">
                          <Check className="h-3 w-3 text-white" />
                        </div>
                      )}
                      {theme.isPremium && (
                        <div className="absolute top-1.5 left-1.5 bg-amber-400 rounded-full px-1.5 py-0.5 flex items-center gap-0.5">
                          <Star className="h-2 w-2 text-white fill-white" />
                          <span className="text-[8px] font-bold text-white uppercase tracking-wide">Pro</span>
                        </div>
                      )}
                    </div>
                    <div className={`px-2.5 py-2 ${isSelected ? 'bg-purple-50' : 'bg-white'}`}>
                      <span className="text-xs font-semibold leading-tight block truncate">{theme.displayName}</span>
                    </div>
                  </button>
                );
              })}
        </div>

        {selectedTheme && (
          <div className="flex items-center gap-2 text-xs text-[#6B21A8] bg-purple-50 border border-purple-100 rounded-lg px-3 py-1.5 w-fit">
            <Check className="h-3 w-3" />
            <span className="font-semibold">{selectedTheme.displayName}</span> selected
          </div>
        )}
      </div>

      <hr className="border-border/50" />

      {/* â”€â”€ Step 2: Photos â”€â”€ */}
      <div className="space-y-3">
        <div>
          <Label className="text-sm font-semibold">
            Child&apos;s Photos *{' '}
            <span className="text-muted-foreground font-normal text-xs">({photos.length}/{MAX_PHOTOS} added)</span>
          </Label>
          <p className="text-xs text-muted-foreground mt-0.5">
            Front-facing, well-lit photos work best â€” we&apos;ll place your child as the star of every page
          </p>
        </div>

        {photos.length === 0 ? (
          <label
            htmlFor="theme-photo-input"
            className={`flex flex-col items-center justify-center gap-2 border-2 border-dashed rounded-2xl p-6 cursor-pointer transition-all ${
              photoError
                ? 'border-red-300 bg-red-50/40 hover:border-red-400'
                : 'border-purple-200 hover:border-[#6B21A8] hover:bg-purple-50/50'
            }`}
          >
            <Camera className="h-8 w-8 text-[#6B21A8]" />
            <span className="text-sm font-medium text-[#6B21A8]">Click to add photos</span>
            <span className="text-xs text-muted-foreground">JPG, PNG, WEBP â€” up to {MAX_PHOTOS} photos</span>
            <input id="theme-photo-input" type="file" accept="image/*" multiple className="hidden" onChange={handleFileChange} />
          </label>
        ) : (
          <div className="flex flex-wrap gap-3">
            {previews.map((src, i) => (
              <div key={i} className="relative w-20 h-20 rounded-xl overflow-hidden group border-2 border-purple-100">
                <Image src={src} alt={`Photo ${i + 1}`} fill className="object-cover" />
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors" />
                <button
                  type="button"
                  onClick={() => removePhoto(i)}
                  className="absolute top-1 right-1 bg-white/90 text-destructive rounded-full w-5 h-5 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-sm"
                >
                  <X className="h-3 w-3" />
                </button>
                <span className="absolute bottom-1 left-1 bg-black/50 text-white text-[9px] font-bold rounded-full px-1.5 py-0.5">{i + 1}</span>
              </div>
            ))}
            {photos.length < MAX_PHOTOS && (
              <label
                htmlFor="theme-photo-input"
                className="w-20 h-20 rounded-xl border-2 border-dashed border-purple-200 flex flex-col items-center justify-center cursor-pointer hover:border-[#6B21A8] hover:bg-purple-50 transition-all"
              >
                <ImagePlus className="h-5 w-5 text-[#6B21A8]" />
                <span className="text-xs text-[#6B21A8] mt-1">Add</span>
                <input id="theme-photo-input" type="file" accept="image/*" multiple className="hidden" onChange={handleFileChange} />
              </label>
            )}
          </div>
        )}

        {photoError && photos.length === 0 && (
          <p className="text-xs text-destructive flex items-center gap-1">
            <AlertCircleIcon className="h-3 w-3" /> At least one photo is required
          </p>
        )}
      </div>

      <hr className="border-border/50" />

      {/* â”€â”€ Step 3: Details + Page count â”€â”€ */}
      <div className="space-y-5">
        <p className="text-sm font-semibold text-foreground">About Your Child</p>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="childName-theme">Child&apos;s Name *</Label>
            <Input id="childName-theme" {...register('childName')} placeholder="e.g. Lily, Max, Amaraâ€¦" className="rounded-xl mt-1" />
            {errors.childName && <p className="text-xs text-destructive mt-1">{errors.childName.message}</p>}
          </div>

          <div>
            <Label htmlFor="age-theme">Age *</Label>
            <Input id="age-theme" type="number" min={1} max={12} {...register('age', { valueAsNumber: true })} placeholder="e.g. 5" className="rounded-xl mt-1" />
            {errors.age && <p className="text-xs text-destructive mt-1">{errors.age.message}</p>}
          </div>

          <div>
            <Label htmlFor="parentEmail-theme">Parent Email *</Label>
            <Input id="parentEmail-theme" type="email" {...register('parentEmail')} placeholder="parent@example.com" className="rounded-xl mt-1" />
            {errors.parentEmail && <p className="text-xs text-destructive mt-1">{errors.parentEmail.message}</p>}
          </div>

          <div>
            <Label htmlFor="whatsappNumber-theme">
              WhatsApp Number
              <span className="text-muted-foreground font-normal text-xs ml-1">(for printed copies)</span>
            </Label>
            <Input id="whatsappNumber-theme" type="tel" {...register('whatsappNumber')} placeholder="+91 98765 43210" className="rounded-xl mt-1" />
            {errors.whatsappNumber && <p className="text-xs text-destructive mt-1">{errors.whatsappNumber.message}</p>}
          </div>
        </div>

        {/* Page count */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <Label className="text-sm font-semibold">Number of Pages</Label>
            <span className="text-xs font-medium text-[#6B21A8] bg-purple-50 border border-purple-100 px-2.5 py-1 rounded-full">
              {pageTier.emoji} {pageCount} pages Â· {pageTier.label}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground w-5 text-center shrink-0">{MIN_PAGES}</span>
            <Slider
              min={MIN_PAGES}
              max={MAX_PAGES}
              step={4}
              value={[pageCount]}
              onValueChange={([v]) => dispatch({ type: 'SET_PAGE_COUNT', payload: v })}
              className="flex-1"
            />
            <span className="text-xs text-muted-foreground w-5 text-center shrink-0">{MAX_PAGES}</span>
          </div>
          <div className="flex justify-between mt-1 px-5">
            {Array.from({ length: (MAX_PAGES - MIN_PAGES) / 4 + 1 }, (_, i) => MIN_PAGES + i * 4).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => dispatch({ type: 'SET_PAGE_COUNT', payload: p })}
                className={`text-[10px] transition-colors ${p === pageCount ? 'text-[#6B21A8] font-bold' : 'text-muted-foreground hover:text-foreground'}`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* â”€â”€ Submit â”€â”€ */}
      <Button
        type="submit"
        disabled={isPending || !selectedTheme || isThemesLoading}
        className="w-full rounded-xl text-base font-semibold py-6 bg-[#6B21A8] hover:bg-[#581C87]"
      >
        {isPending ? (
          <><Loader className="mr-2 h-5 w-5 animate-spin" /> Crafting your personalised bookâ€¦</>
        ) : (
          <><Sparkles className="mr-2 h-5 w-5" /> Create My Coloring Book</>
        )}
      </Button>
    </form>
  );
}
