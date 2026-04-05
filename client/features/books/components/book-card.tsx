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
        <div className="relative aspect-video sm:aspect-[3/4] overflow-hidden">
          <Image
            src={book.coverImage}
            alt={book.title}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
          <div className="absolute top-2 right-2 md:top-3 md:right-3 flex gap-1.5 md:gap-2">
            <Badge className="bg-white/90 text-foreground text-xs px-1.5 py-0.5 md:px-2 md:py-1">
              {book.ageGroup}
            </Badge>
            {isStoryBook && book.type === 'series' && (
              <Badge className="bg-primary/90 text-xs px-1.5 py-0.5 md:px-2 md:py-1">Series</Badge>
            )}
          </div>
        </div>

        <CardContent className="flex-1 p-3 md:p-6">
          <Badge variant="outline" className="mb-1.5 md:mb-2 text-xs">
            {book.genre}
          </Badge>
          <h3 className="text-sm md:text-xl font-bold mb-1 md:mb-2 line-clamp-2">{book.title}</h3>
          <p className="text-xs md:text-sm text-muted-foreground mb-2 md:mb-3 line-clamp-2 md:line-clamp-3">
            {book.description}
          </p>
          <div className="flex items-center justify-between">
            <span className="text-base md:text-2xl font-bold text-primary">
              ₹{book.price}
            </span>
            <span className="text-xs text-muted-foreground">
              {book.totalPages} pages
            </span>
          </div>
        </CardContent>

        <CardFooter className="p-3 md:p-6 pt-0 flex gap-2">
          <Link href={`/preview/${book.id}`} className="flex-1">
            <Button variant="outline" size="sm" className="w-full rounded-xl text-xs md:text-sm h-8 md:h-10">
              <Eye className="mr-1 md:mr-2 h-3 w-3 md:h-4 md:w-4" />
              Preview
            </Button>
          </Link>
          <Link href={`/create/${book.id}`} className="flex-1">
            <Button size="sm" className="w-full rounded-xl text-xs md:text-sm h-8 md:h-10">
              <Sparkles className="mr-1 md:mr-2 h-3 w-3 md:h-4 md:w-4" />
              Create
            </Button>
          </Link>
        </CardFooter>
      </Card>
    </motion.div>
  );
}
