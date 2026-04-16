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
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { BookCard } from '@/features/books/components/book-card';
import { BookFiltersComponent } from '@/features/books/components/book-filters';
import { useStoryBooks } from '@/features/books/hooks/useBooks';
import { useBookFilters } from '@/features/books/hooks/useBookFilters';
import { BookFilters, SortOption } from '@/types/book.types';
import { Search, SlidersHorizontal } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

export default function StoryBooksPage() {
  const { data: books, isLoading, error } = useStoryBooks();
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<BookFilters>({});
  const [sortBy, setSortBy] = useState<SortOption>('title');

  const filteredBooks = useBookFilters(books, filters, searchQuery, sortBy);

  const activeFilterCount = [
    filters.ageGroup?.length ? 'age' : undefined,
    filters.genre?.length ? 'genre' : undefined,
    filters.type?.length ? 'type' : undefined,
    filters.minPrice !== undefined || filters.maxPrice !== undefined ? 'price' : undefined,
  ].filter(Boolean).length;

  return (
    <div className="min-h-screen relative">
      <main className="relative z-10 container mx-auto px-4 py-6 md:py-8">
        <div className="mb-6 md:mb-8">
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-3 bg-gradient-to-r from-pink-500 to-purple-500 bg-clip-text text-transparent">
            Personalized Story Books
          </h1>
          <p className="text-base md:text-lg text-muted-foreground">
            Create magical adventures where your child is the hero
          </p>
        </div>

        {/* Search + Sort + Mobile filter trigger */}
        <div className="flex gap-3 mb-6 md:mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-muted-foreground h-10 w-4 pointer-events-none" />
            <Input
              placeholder="Search by title, genre, theme…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 h-11 rounded-2xl bg-background border-border/60 shadow-sm focus-visible:ring-pink-400/50 text-sm"
            />
          </div>

          {/* Mobile filter button */}
          <Sheet>
            <SheetTrigger asChild>
              <Button
                variant="outline"
                className="lg:hidden relative h-11 px-3.5 rounded-2xl border-border/60 shadow-sm shrink-0"
                aria-label="Open filters"
              >
                <SlidersHorizontal className="h-4 w-4" />
                {activeFilterCount > 0 && (
                  <Badge className="absolute -top-1.5 -right-1.5 h-4 min-w-4 px-1 text-[10px] bg-gradient-to-r from-pink-500 to-purple-500 text-white border-0 leading-none flex items-center justify-center">
                    {activeFilterCount}
                  </Badge>
                )}
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-[85vw] max-w-sm p-0 flex flex-col">
              <SheetHeader className="px-5 pt-5 pb-3 border-b shrink-0">
                <SheetTitle className="text-base font-semibold">Filters</SheetTitle>
              </SheetHeader>
              <div className="flex-1 overflow-y-auto px-5 py-4">
                <BookFiltersComponent
                  filters={filters}
                  onFiltersChange={setFilters}
                  showTypeFilter={true}
                  className="static"
                />
              </div>
            </SheetContent>
          </Sheet>

          <Select value={sortBy} onValueChange={(value) => setSortBy(value as SortOption)}>
            <SelectTrigger className="w-[140px] sm:w-[190px] h-11 rounded-2xl bg-background border-border/60 shadow-sm text-sm shrink-0">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              <SelectItem value="title">Title A–Z</SelectItem>
              <SelectItem value="price-asc">Price: Low to High</SelectItem>
              <SelectItem value="price-desc">Price: High to Low</SelectItem>
              <SelectItem value="newest">Newest First</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid lg:grid-cols-[260px_1fr] gap-8">
          {/* Desktop sidebar */}
          <aside className="hidden lg:block">
            <BookFiltersComponent
              filters={filters}
              onFiltersChange={setFilters}
              showTypeFilter={true}
            />
          </aside>

          <div>
            {isLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 md:gap-6">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="space-y-3">
                    <Skeleton className="aspect-[3/4] w-full rounded-3xl" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                  </div>
                ))}
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <p className="text-base md:text-lg text-muted-foreground">
                  Oops! Something went wrong. Please try again later.
                </p>
              </div>
            ) : filteredBooks.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-base md:text-lg text-muted-foreground">
                  No books found matching your criteria. Try adjusting your filters.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 md:gap-6">
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
