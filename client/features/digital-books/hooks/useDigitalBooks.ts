import { useMutation, useQuery } from '@tanstack/react-query';

import { digitalBooksService } from '@/features/digital-books/services/digital-books.service';
import { DigitalBookFilters, SendDigitalBookEmailPayload } from '@/features/digital-books/types/digital-book.types';

export const DIGITAL_BOOK_QUERY_KEYS = {
  books: (filters: DigitalBookFilters) => ['digitalBooks', filters] as const,
  details: (bookId: number) => ['digitalBook', bookId] as const,
  filterOptions: () => ['digitalBookFilterOptions'] as const,
};

export function useDigitalBooks(filters: DigitalBookFilters = {}) {
  return useQuery({
    queryKey: DIGITAL_BOOK_QUERY_KEYS.books(filters),
    queryFn: () => digitalBooksService.getBooks(filters),
    staleTime: 1000 * 60 * 3,
  });
}

export function useDigitalBookDetails(bookId: number) {
  return useQuery({
    queryKey: DIGITAL_BOOK_QUERY_KEYS.details(bookId),
    queryFn: () => digitalBooksService.getBookById(bookId),
    enabled: Number.isFinite(bookId) && bookId > 0,
    staleTime: 1000 * 60 * 5,
  });
}

export function useDigitalBookFilterOptions() {
  return useQuery({
    queryKey: DIGITAL_BOOK_QUERY_KEYS.filterOptions(),
    queryFn: digitalBooksService.getFilterOptions,
    staleTime: 1000 * 60 * 10,
  });
}

export function useSendDigitalBookToEmail() {
  return useMutation({
    mutationFn: (payload: SendDigitalBookEmailPayload) => digitalBooksService.sendBookToEmail(payload),
  });
}
