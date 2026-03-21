import { useQuery, useMutation } from '@tanstack/react-query';
import { booksService } from '../services/books.service';
import { GenerateBookRequest } from '@/types/book.types';

export const useStoryBooks = () => {
  return useQuery({
    queryKey: ['storyBooks'],
    queryFn: booksService.getAllStoryBooks,
  });
};

export const useColoringBooks = () => {
  return useQuery({
    queryKey: ['coloringBooks'],
    queryFn: booksService.getAllColoringBooks,
  });
};

export const useStoryBook = (id: string) => {
  return useQuery({
    queryKey: ['storyBook', id],
    queryFn: () => booksService.getStoryBookById(id),
    enabled: !!id,
  });
};

export const useColoringBook = (id: string) => {
  return useQuery({
    queryKey: ['coloringBook', id],
    queryFn: () => booksService.getColoringBookById(id),
    enabled: !!id,
  });
};

export const useGenerateBook = () => {
  return useMutation({
    mutationFn: (request: GenerateBookRequest) => booksService.generateBook(request),
  });
};

export const useBookPreview = (bookId: string) => {
  return useQuery({
    queryKey: ['bookPreview', bookId],
    queryFn: () => booksService.getBookPreview(bookId),
    enabled: !!bookId,
  });
};
