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
import { useStoryBook, useColoringBook, useGenerateBook } from '@/features/books/hooks/useBooks';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Loader as Loader2, Upload, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import Image from 'next/image';
import { useState } from 'react';

const createBookSchema = z.object({
  childName: z.string().min(1, 'Child name is required').max(50),
  age: z.number().min(1).max(12),
  gender: z.enum(['boy', 'girl', 'other']),
  parentEmail: z.string().email('Invalid email address'),
  photos: z.any().optional(),
});

type CreateBookFormData = z.infer<typeof createBookSchema>;

export default function CreateBookPage() {
  const params = useParams();
  const router = useRouter();
  const bookId = params.bookId as string;
  const [photoFiles, setPhotoFiles] = useState<File[]>([]);

  const { data: storyBook } = useStoryBook(bookId);
  const { data: coloringBook } = useColoringBook(bookId);
  const book = storyBook || coloringBook;

  const { mutate: generateBook, isPending } = useGenerateBook();

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<CreateBookFormData>({
    resolver: zodResolver(createBookSchema),
    defaultValues: {
      age: 5,
      gender: 'boy',
    },
  });

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length + photoFiles.length > 3) {
      toast.error('You can only upload up to 3 photos');
      return;
    }
    setPhotoFiles([...photoFiles, ...files.slice(0, 3 - photoFiles.length)]);
  };

  const removePhoto = (index: number) => {
    setPhotoFiles(photoFiles.filter((_, i) => i !== index));
  };

  const onSubmit = (data: CreateBookFormData) => {
    generateBook(
      {
        templateId: bookId,
        childName: data.childName,
        age: data.age,
        gender: data.gender,
        parentEmail: data.parentEmail,
        photos: photoFiles,
      },
      {
        onSuccess: (generatedBook) => {
          toast.success('Your book is blooming!');
          router.push(`/preview/${generatedBook.id}`);
        },
        onError: () => {
          toast.error('Failed to create book. Please try again.');
        },
      }
    );
  };

  if (!book) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
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
            Create Your Personalized Book
          </h1>
          <p className="text-center text-muted-foreground mb-8">
            Tell us about your little hero to create their magical adventure
          </p>

          <div className="grid md:grid-cols-2 gap-8">
            <Card className="rounded-3xl shadow-lg overflow-hidden">
              <div className="relative aspect-[3/4]">
                <Image
                  src={book.coverImage}
                  alt={book.title}
                  fill
                  className="object-cover"
                />
              </div>
              <CardContent className="p-6">
                <h2 className="text-2xl font-bold mb-2">{book.title}</h2>
                <p className="text-muted-foreground">{book.description}</p>
              </CardContent>
            </Card>

            <Card className="rounded-3xl shadow-lg">
              <CardHeader>
                <CardTitle>Book Details</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                  <div>
                    <Label htmlFor="childName">Child's Name *</Label>
                    <Input
                      id="childName"
                      {...register('childName')}
                      placeholder="Enter child's name"
                      className="rounded-xl"
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
                      {...register('age', { valueAsNumber: true })}
                      placeholder="5"
                      className="rounded-xl"
                    />
                    {errors.age && (
                      <p className="text-sm text-destructive mt-1">{errors.age.message}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="gender">Gender *</Label>
                    <Select
                      onValueChange={(value) => setValue('gender', value as any)}
                      defaultValue="boy"
                    >
                      <SelectTrigger className="rounded-xl">
                        <SelectValue placeholder="Select gender" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="boy">Boy</SelectItem>
                        <SelectItem value="girl">Girl</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="parentEmail">Parent Email *</Label>
                    <Input
                      id="parentEmail"
                      type="email"
                      {...register('parentEmail')}
                      placeholder="parent@example.com"
                      className="rounded-xl"
                    />
                    {errors.parentEmail && (
                      <p className="text-sm text-destructive mt-1">{errors.parentEmail.message}</p>
                    )}
                  </div>

                  <div>
                    <Label>Upload Photos (Optional, up to 3)</Label>
                    <div className="mt-2">
                      <label
                        htmlFor="photos"
                        className="flex items-center justify-center border-2 border-dashed rounded-xl p-6 cursor-pointer hover:border-primary transition"
                      >
                        <div className="text-center">
                          <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                          <p className="text-sm text-muted-foreground">
                            Click to upload photos
                          </p>
                        </div>
                        <input
                          id="photos"
                          type="file"
                          accept="image/*"
                          multiple
                          onChange={handlePhotoUpload}
                          className="hidden"
                        />
                      </label>
                    </div>
                    {photoFiles.length > 0 && (
                      <div className="grid grid-cols-3 gap-2 mt-4">
                        {photoFiles.map((file, index) => (
                          <div key={index} className="relative aspect-square">
                            <Image
                              src={URL.createObjectURL(file)}
                              alt={`Photo ${index + 1}`}
                              fill
                              className="object-cover rounded-lg"
                            />
                            <button
                              type="button"
                              onClick={() => removePhoto(index)}
                              className="absolute top-1 right-1 bg-destructive text-white rounded-full w-6 h-6 flex items-center justify-center text-xs"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <Button
                    type="submit"
                    className="w-full rounded-xl text-lg py-6"
                    disabled={isPending}
                  >
                    {isPending ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                        Your book is blooming...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-5 w-5" />
                        Create My Book
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
