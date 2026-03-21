import { useMemo } from 'react';
import { StoryBook, ColoringBook, BookFilters, SortOption } from '@/types/book.types';

export function useBookFilters<T extends StoryBook | ColoringBook>(
  books: T[] | undefined,
  filters: BookFilters,
  searchQuery: string,
  sortBy: SortOption
) {
  return useMemo(() => {
    if (!books) return [];

    let filtered = books.filter((book) => {
      if (searchQuery && !book.title.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }

      if (filters.ageGroup && book.ageGroup !== filters.ageGroup) {
        return false;
      }

      if (filters.genre && book.genre !== filters.genre) {
        return false;
      }

      if ('type' in book && filters.type && book.type !== filters.type) {
        return false;
      }

      if (filters.minPrice !== undefined && book.price < filters.minPrice) {
        return false;
      }

      if (filters.maxPrice !== undefined && book.price > filters.maxPrice) {
        return false;
      }

      return true;
    });

    filtered = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'title':
          return a.title.localeCompare(b.title);
        case 'price-asc':
          return a.price - b.price;
        case 'price-desc':
          return b.price - a.price;
        case 'newest':
          return 0;
        default:
          return 0;
      }
    });

    return filtered;
  }, [books, filters, searchQuery, sortBy]);
}
