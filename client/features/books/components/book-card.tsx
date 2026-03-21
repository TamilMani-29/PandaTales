'use client';

import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { StoryBook, ColoringBook } from '@/types/book.types';
import Link from 'next/link';
import Image from 'next/image';
import { Eye, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

type BookCardProps = {
  book: StoryBook | ColoringBook;
  type: 'story' | 'coloring';
};

export function BookCard({ book, type }: BookCardProps) {
  const isStoryBook = 'type' in book;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.02 }}
    >
      <Card className="h-full flex flex-col overflow-hidden rounded-3xl shadow-lg hover:shadow-xl transition-all border-2">
        <div className="relative aspect-[3/4] overflow-hidden">
          <Image
            src={book.coverImage}
            alt={book.title}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
          <div className="absolute top-3 right-3 flex gap-2">
            <Badge className="bg-white/90 text-foreground">
              {book.ageGroup}
            </Badge>
            {isStoryBook && book.type === 'series' && (
              <Badge className="bg-primary/90">Series</Badge>
            )}
          </div>
        </div>

        <CardContent className="flex-1 p-6">
          <Badge variant="outline" className="mb-2">
            {book.genre}
          </Badge>
          <h3 className="text-xl font-bold mb-2 line-clamp-2">{book.title}</h3>
          <p className="text-sm text-muted-foreground mb-3 line-clamp-3">
            {book.description}
          </p>
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-primary">
              ₹{book.price}
            </span>
            <span className="text-sm text-muted-foreground">
              {book.totalPages} pages
            </span>
          </div>
        </CardContent>

        <CardFooter className="p-6 pt-0 flex gap-2">
          <Link href={`/preview/${book.id}`} className="flex-1">
            <Button variant="outline" className="w-full rounded-xl">
              <Eye className="mr-2 h-4 w-4" />
              Preview
            </Button>
          </Link>
          <Link href={`/create/${book.id}`} className="flex-1">
            <Button className="w-full rounded-xl">
              <Sparkles className="mr-2 h-4 w-4" />
              Create
            </Button>
          </Link>
        </CardFooter>
      </Card>
    </motion.div>
  );
}
