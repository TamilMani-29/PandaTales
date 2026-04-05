import { useQuery, useMutation } from '@tanstack/react-query';
import { booksService } from '../services/books.service';
import { GenerateBookRequest } from '@/types/book.types';

export const useStoryBooks = () => {
  return useQuery({
    queryKey: ['storyBooks'],
    queryFn: booksService.getAllStoryBooks,
    staleTime: 5 * 60 * 1000,
  });
};

export const useColoringBooks = () => {
  return useQuery({
    queryKey: ['coloringBooks'],
    queryFn: booksService.getAllColoringBooks,
    staleTime: 5 * 60 * 1000,
  });
};

export const useStoryBook = (id: string) => {
  return useQuery({
    queryKey: ['storyBook', id],
    queryFn: () => booksService.getStoryBookById(id),
    enabled: !!id,
    staleTime: 10 * 60 * 1000,
    retry: false, // Don't retry on 404
    throwOnError: false, // Fail silently for checkout page fallback pattern
  });
};

export const useColoringBook = (id: string) => {
  return useQuery({
    queryKey: ['coloringBook', id],
    queryFn: () => booksService.getColoringBookById(id),
    enabled: !!id,
    staleTime: 10 * 60 * 1000,
    retry: false, // Don't retry on 404
    throwOnError: false, // Fail silently for checkout page fallback pattern
  });
};

/** Mutation that returns { id: string (generation_id), status: string } */
export const useGenerateBook = () => {
  return useMutation({
    mutationFn: (request: GenerateBookRequest) => booksService.generateBook(request),
  });
};

/**
 * Preview data for a generated book.
 * Polls every 3 s until status = 'completed' or 'failed'.
 */
export const useBookPreview = (bookId: string) => {
  return useQuery({
    queryKey: ['bookPreview', bookId],
    queryFn: () => booksService.getBookPreview(bookId),
    enabled: !!bookId,
    staleTime: 0,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'completed' || status === 'failed' || status === 'cancelled') {
        return false;
      }
      return 3000;
    },
  });
};
