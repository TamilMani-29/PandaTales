'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { BookCard } from '@/features/books/components/book-card';
import { BookFiltersComponent } from '@/features/books/components/book-filters';
import { useStoryBooks } from '@/features/books/hooks/useBooks';
import { useBookFilters } from '@/features/books/hooks/useBookFilters';
import { BookFilters, SortOption } from '@/types/book.types';
import { Search, Loader2 } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

export default function StoryBooksPage() {
  const { data: books, isLoading, error } = useStoryBooks();
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<BookFilters>({});
  const [sortBy, setSortBy] = useState<SortOption>('title');

  const filteredBooks = useBookFilters(books, filters, searchQuery, sortBy);

  return (
    <div className="min-h-screen relative">
      <main className="relative z-10 container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-pink-500 to-purple-500 bg-clip-text text-transparent">
            Personalized Story Books
          </h1>
          <p className="text-lg text-muted-foreground">
            Create magical adventures where your child is the hero
          </p>
        </div>

        <div className="flex gap-4 mb-6 flex-col md:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-5 w-5" />
            <Input
              placeholder="Search books..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 rounded-2xl"
            />
          </div>
          <Select value={sortBy} onValueChange={(value) => setSortBy(value as SortOption)}>
            <SelectTrigger className="w-full md:w-[200px] rounded-2xl">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="title">Title</SelectItem>
              <SelectItem value="price-asc">Price: Low to High</SelectItem>
              <SelectItem value="price-desc">Price: High to Low</SelectItem>
              <SelectItem value="newest">Newest</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid lg:grid-cols-[300px_1fr] gap-8">
          <aside className="hidden lg:block">
            <BookFiltersComponent
              filters={filters}
              onFiltersChange={setFilters}
              showTypeFilter={true}
            />
          </aside>

          <div>
            {isLoading ? (
              <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="space-y-4">
                    <Skeleton className="aspect-[3/4] w-full rounded-3xl" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                  </div>
                ))}
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <p className="text-lg text-muted-foreground">
                  Oops! Something went wrong. Please try again later.
                </p>
              </div>
            ) : filteredBooks.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-lg text-muted-foreground">
                  No books found matching your criteria. Try adjusting your filters.
                </p>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
                {filteredBooks.map((book) => (
                  <BookCard key={book.id} book={book} type="story" />
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
