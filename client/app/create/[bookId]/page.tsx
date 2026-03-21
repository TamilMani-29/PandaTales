'use client';

import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useStoryBook, useGenerateBook } from '@/features/books/hooks/useBooks';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Loader2, Upload, Sparkles, X, ImagePlus, ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import Image from 'next/image';
import { useState, useEffect, useMemo } from 'react';
import { Badge } from '@/components/ui/badge';

const createBookSchema = z.object({
  childName: z.string().min(1, 'Child name is required').max(50),
  childAge: z.number({ invalid_type_error: 'Age must be a number' }).min(1).max(12),
  childGender: z.enum(['male', 'female', 'other']),
  parentEmail: z.string().min(1, 'Email is required').email('Invalid email address'),
  whatsappNumber: z.string().regex(/^[0-9+\s\-]{7,20}$/, 'Enter a valid WhatsApp number').optional().or(z.literal('')),
});

type CreateBookFormData = z.infer<typeof createBookSchema>;

export default function CreateBookPage() {
  const params = useParams();
  const router = useRouter();
  const bookId = params.bookId as string;

  const { data: storyBook, isLoading: bookLoading } = useStoryBook(bookId);
  const { mutate: generateBook, isPending } = useGenerateBook();

  const [photoFiles, setPhotoFiles] = useState<File[]>([]);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const [activeSlide, setActiveSlide] = useState(0);

  const allImages = useMemo(() => {
    if (!storyBook) return [];
    return [storyBook.coverImage, ...storyBook.previewImages].filter(Boolean).slice(0, 5);
  }, [storyBook]);

  useEffect(() => {
    if (allImages.length <= 1) return;
    const timer = setInterval(() => {
      setActiveSlide((prev) => (prev + 1) % allImages.length);
    }, 3000);
    return () => clearInterval(timer);
  }, [allImages.length]);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<CreateBookFormData>({
    resolver: zodResolver(createBookSchema),
    defaultValues: {
      childAge: 5,
      childGender: 'male',
    },
  });

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const remaining = 3 - photoFiles.length;
    if (remaining <= 0) return;
    setPhotoFiles((prev) => [...prev, ...files.slice(0, remaining)]);
    setPhotoError(null);
    e.target.value = '';
  };

  const removePhoto = (index: number) => {
    setPhotoFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const onSubmit = (data: CreateBookFormData) => {
    if (photoFiles.length === 0) {
      setPhotoError('Please upload at least 1 photo of your child to personalise the book.');
      return;
    }

    generateBook(
      {
        templateId: bookId,
        childName: data.childName,
        childAge: data.childAge,
        childGender: data.childGender,
        parentEmail: data.parentEmail,
        whatsappNumber: data.whatsappNumber || undefined,
        photos: photoFiles,
      },
      {
        onSuccess: (result) => {
          toast.success('Your story book is being created!', {
            description: 'This usually takes 30–60 seconds.',
          });
          router.push(`/preview/${result.id}`);
        },
        onError: (err: unknown) => {
          const message =
            err instanceof Error ? err.message : 'Failed to create book. Please try again.';
          toast.error(message);
        },
      }
    );
  };

  if (bookLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!storyBook) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-muted-foreground mb-4">Book template not found.</p>
          <Button onClick={() => router.push('/story-books')}>Browse Story Books</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative">
      <main className="relative z-10 container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto"
        >
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-center bg-gradient-to-r from-[#6B21A8] to-[#C9A227] bg-clip-text text-transparent">
            Create Your Story Book
          </h1>
          <p className="text-center text-muted-foreground mb-8">
            Personalise <span className="font-semibold">&ldquo;{storyBook.title}&rdquo;</span> for your little hero
          </p>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Book preview card */}
            <Card className="rounded-3xl shadow-lg overflow-hidden">
              <div className="relative aspect-[3/4] overflow-hidden">
                {allImages.map((src, idx) => (
                  <Image
                    key={idx}
                    src={src}
                    alt={`${storyBook.title} — preview ${idx + 1}`}
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
                        className={`w-2 h-2 rounded-full transition-all duration-300 ${
                          idx === activeSlide ? 'bg-white scale-125' : 'bg-white/50'
                        }`}
                        aria-label={`Go to image ${idx + 1}`}
                      />
                    ))}
                  </div>
                )}

                {/* Badges */}
                <div className="absolute top-3 right-3 flex gap-2 z-10">
                  <Badge className="bg-white/90 text-foreground text-xs">{storyBook.ageGroup}</Badge>
                  {storyBook.type === 'series' && (
                    <Badge className="bg-primary/90 text-xs">Series</Badge>
                  )}
                </div>
              </div>
              <CardContent className="p-6">
                <Badge variant="outline" className="mb-2 capitalize">{storyBook.genre}</Badge>
                <h2 className="text-xl font-bold mb-2">{storyBook.title}</h2>
                <p className="text-sm text-muted-foreground line-clamp-3">{storyBook.description}</p>
                <div className="flex items-center justify-between mt-3">
                  <span className="text-2xl font-bold text-primary">₹{storyBook.price}</span>
                  <span className="text-sm text-muted-foreground">{storyBook.totalPages} pages</span>
                </div>
              </CardContent>
            </Card>

            {/* Creation form */}
            <Card className="rounded-3xl shadow-lg">
              <CardHeader>
                <CardTitle>Child&apos;s Details</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                  {/* Child Name */}
                  <div>
                    <Label htmlFor="childName">Child&apos;s Name *</Label>
                    <Input
                      id="childName"
                      {...register('childName')}
                      placeholder="e.g. Emma"
                      className="rounded-xl mt-1"
                    />
                    {errors.childName && (
                      <p className="text-sm text-destructive mt-1">{errors.childName.message}</p>
                    )}
                  </div>

                  {/* Age */}
                  <div>
                    <Label htmlFor="childAge">Age *</Label>
                    <Input
                      id="childAge"
                      type="number"
                      min={1}
                      max={12}
                      {...register('childAge', { valueAsNumber: true })}
                      placeholder="5"
                      className="rounded-xl mt-1"
                    />
                    {errors.childAge && (
                      <p className="text-sm text-destructive mt-1">{errors.childAge.message}</p>
                    )}
                  </div>

                  {/* Gender */}
                  <div>
                    <Label>Gender *</Label>
                    <Select
                      defaultValue="male"
                      onValueChange={(value) =>
                        setValue('childGender', value as 'male' | 'female' | 'other')
                      }
                    >
                      <SelectTrigger className="rounded-xl mt-1">
                        <SelectValue placeholder="Select gender" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="male">Boy</SelectItem>
                        <SelectItem value="female">Girl</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Parent Email */}
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

                  {/* WhatsApp */}
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

                  {/* Photo Upload */}
                  <div>
                    <Label>
                      Child&apos;s Photo(s) *{' '}
                      <span className="text-muted-foreground font-normal text-xs">(1–3 photos)</span>
                    </Label>
                    <p className="text-xs text-muted-foreground mt-0.5 mb-2">
                      Photos help personalise illustrations in the story.
                    </p>

                    {photoFiles.length > 0 && (
                      <div className="flex flex-wrap gap-3 mb-3">
                        {photoFiles.map((file, idx) => (
                          <div
                            key={idx}
                            className="relative w-20 h-20 rounded-xl overflow-hidden border-2 border-border group"
                          >
                            <Image
                              src={URL.createObjectURL(file)}
                              alt={`Photo ${idx + 1}`}
                              fill
                              className="object-cover"
                            />
                            <button
                              type="button"
                              onClick={() => removePhoto(idx)}
                              className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </div>
                        ))}
                        {photoFiles.length < 3 && (
                          <label
                            htmlFor="photo-upload"
                            className="w-20 h-20 rounded-xl border-2 border-dashed border-border flex flex-col items-center justify-center cursor-pointer hover:border-primary transition-colors"
                          >
                            <ImagePlus className="h-5 w-5 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground mt-1">Add</span>
                          </label>
                        )}
                      </div>
                    )}

                    {photoFiles.length === 0 && (
                      <label
                        htmlFor="photo-upload"
                        className={`flex flex-col items-center justify-center w-full h-32 rounded-xl border-2 border-dashed cursor-pointer transition-colors ${
                          photoError
                            ? 'border-destructive bg-red-50'
                            : 'border-border hover:border-primary'
                        }`}
                      >
                        <Upload className="h-6 w-6 text-muted-foreground mb-2" />
                        <span className="text-sm text-muted-foreground">Click to upload photos</span>
                        <span className="text-xs text-muted-foreground mt-1">
                          PNG, JPG up to 10 MB each
                        </span>
                      </label>
                    )}

                    <input
                      id="photo-upload"
                      type="file"
                      accept="image/*"
                      multiple
                      className="hidden"
                      onChange={handlePhotoUpload}
                    />

                    {photoError && (
                      <p className="text-sm text-destructive mt-1">{photoError}</p>
                    )}
                  </div>

                  {/* Submit */}
                  <Button
                    type="submit"
                    disabled={isPending}
                    className="w-full rounded-xl py-6 text-base bg-[#6B21A8] hover:bg-[#581C87] gap-2"
                  >
                    {isPending ? (
                      <>
                        <Loader2 className="h-5 w-5 animate-spin" />
                        Creating your book…
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-5 w-5" />
                        Create My Story Book
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
