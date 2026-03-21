'use client';

import { useState } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Upload, X, ImagePlus, Sparkles, Loader, Phone } from 'lucide-react';
import { toast } from 'sonner';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { PhotoColoringSubmitData } from '@/types/book.types';

const MAX_PHOTOS = 10;

const schema = z.object({
  childName: z.string().min(1, 'Child name is required').max(50),
  age: z.number({ invalid_type_error: 'Age is required' }).min(1).max(12),
  parentEmail: z.string().email('Invalid email address'),
  whatsappNumber: z.string().regex(/^[0-9+\s\-]{7,20}$/, 'Enter a valid WhatsApp number').optional().or(z.literal('')),
});

type FormData = z.infer<typeof schema>;

type Props = {
  onSubmit: (data: PhotoColoringSubmitData) => void;
  isPending: boolean;
};

export function PhotoUploadMode({ onSubmit, isPending }: Props) {
  const [photos, setPhotos] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { age: 5 },
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
    e.target.value = '';
  };

  const removePhoto = (index: number) => {
    URL.revokeObjectURL(previews[index]);
    setPhotos((prev) => prev.filter((_, i) => i !== index));
    setPreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const onFormSubmit = (data: FormData) => {
    if (photos.length === 0) {
      toast.error('Please upload at least one photo');
      return;
    }
    onSubmit({
      childName: data.childName,
      childAge: data.age,
      parentEmail: data.parentEmail,
      whatsappNumber: data.whatsappNumber || undefined,
      photos,
    });
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-8">
      <div className="grid md:grid-cols-2 gap-8">
        <div className="space-y-5">
          <div>
            <Label htmlFor="childName">Child's Name *</Label>
            <Input
              id="childName"
              {...register('childName')}
              placeholder="Enter child's name"
              className="rounded-xl mt-1"
            />
            {errors.childName && (
              <p className="text-sm text-destructive mt-1">{errors.childName.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="age">Age *</Label>
            <Input
              id="age"
              type="number"
              min={1}
              max={12}
              {...register('age', { valueAsNumber: true })}
              placeholder="5"
              className="rounded-xl mt-1"
            />
            {errors.age && (
              <p className="text-sm text-destructive mt-1">{errors.age.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="parentEmail">Parent Email *</Label>
            <Input
              id="parentEmail"
              type="email"
              {...register('parentEmail')}
              placeholder="parent@example.com"
              className="rounded-xl mt-1"
            />
            {errors.parentEmail && (
              <p className="text-sm text-destructive mt-1">{errors.parentEmail.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="whatsappNumber">
              WhatsApp Number
              <span className="text-muted-foreground font-normal text-xs ml-1">(required for printed copies)</span>
            </Label>
            <Input
              id="whatsappNumber"
              type="tel"
              {...register('whatsappNumber')}
              placeholder="+91 98765 43210"
              className="rounded-xl mt-1"
            />
            {errors.whatsappNumber && (
              <p className="text-sm text-destructive mt-1">{errors.whatsappNumber.message}</p>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <Label>
              Upload Photos *{' '}
              <span className="text-muted-foreground font-normal text-sm">
                ({photos.length}/{MAX_PHOTOS} uploaded)
              </span>
            </Label>
            <p className="text-xs text-muted-foreground mt-0.5 mb-3">
              We'll convert each photo into a unique coloring page for your child
            </p>

            {photos.length === 0 && (
              <label
                htmlFor="photo-input"
                className="flex flex-col items-center justify-center border-2 border-dashed border-purple-200 rounded-2xl p-6 cursor-pointer hover:border-primary hover:bg-purple-50/50 transition-colors"
              >
                <ImagePlus className="h-10 w-10 text-[#6B21A8] mb-2" />
                <span className="text-sm font-medium text-[#6B21A8]">Click to add photos</span>
                <span className="text-xs text-muted-foreground mt-1">
                  JPG, PNG, WEBP — up to {MAX_PHOTOS} photos
                </span>
                <input
                  id="photo-input"
                  type="file"
                  accept="image/*"
                  multiple
                  className="hidden"
                  onChange={handleFileChange}
                />
              </label>
            )}
          </div>

          {previews.length > 0 && (
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
                  <span className="absolute bottom-1 left-1 bg-black/50 text-white text-[9px] font-bold rounded-full px-1.5 py-0.5">
                    {i + 1}
                  </span>
                </div>
              ))}
              {photos.length < MAX_PHOTOS && (
                <label
                  htmlFor="photo-input"
                  className="w-20 h-20 rounded-xl border-2 border-dashed border-purple-200 flex flex-col items-center justify-center cursor-pointer hover:border-[#6B21A8] hover:bg-purple-50 transition-all"
                >
                  <ImagePlus className="h-5 w-5 text-[#6B21A8]" />
                  <span className="text-xs text-[#6B21A8] mt-1">Add</span>
                </label>
              )}
            </div>
          )}
        </div>
      </div>

      <Card className="bg-purple-50/60 border-purple-100 rounded-2xl">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Upload className="h-5 w-5 text-[#6B21A8] mt-0.5 flex-shrink-0" />
            <div className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">How it works:</span> Each photo you upload becomes one coloring page. We convert the photo into a clean outline illustration perfect for coloring. Upload up to {MAX_PHOTOS} photos to get up to {MAX_PHOTOS} unique coloring pages.
            </div>
          </div>
        </CardContent>
      </Card>

      <Button
        type="submit"
        disabled={isPending || photos.length === 0}
        className="w-full rounded-xl text-lg py-6 bg-[#6B21A8] hover:bg-[#581C87]"
      >
        {isPending ? (
          <>
            <Loader className="mr-2 h-5 w-5 animate-spin" />
            Generating your coloring pages...
          </>
        ) : (
          <>
            <Sparkles className="mr-2 h-5 w-5" />
            Generate Coloring Pages ({photos.length} {photos.length === 1 ? 'page' : 'pages'})
          </>
        )}
      </Button>
    </form>
  );
}
