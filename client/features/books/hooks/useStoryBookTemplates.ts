import { useQuery, useMutation } from '@tanstack/react-query';
import { storyBookTemplatesService } from '../services/story-book-templates.service';
import { StoryTemplateFilters, GenerateBookRequest } from '@/types/book.types';

/**
 * Paginated list of story book templates (server-side filtered).
 */
export function useStoryBookTemplates(filters: StoryTemplateFilters = {}) {
  return useQuery({
    queryKey: ['storyBookTemplates', filters],
    queryFn: () => storyBookTemplatesService.getTemplates(filters),
    staleTime: 5 * 60 * 1000, // 5 min
  });
}

/**
 * Full detail for a single story book template.
 */
export function useStoryBookTemplate(id: string) {
  return useQuery({
    queryKey: ['storyBookTemplate', id],
    queryFn: () => storyBookTemplatesService.getTemplateById(id),
    enabled: !!id,
    staleTime: 10 * 60 * 1000, // 10 min
  });
}

/**
 * List of available genres.
 */
export function useStoryBookGenresList() {
  return useQuery({
    queryKey: ['storyBookGenres'],
    queryFn: () => storyBookTemplatesService.getGenresList(),
    staleTime: 15 * 60 * 1000, // 15 min
  });
}

/**
 * Mutation to initiate story book generation.
 * Returns { id: string (generation_id), status: string }.
 */
export function useGenerateStoryBook() {
  return useMutation({
    mutationFn: (request: GenerateBookRequest) =>
      storyBookTemplatesService.generateStoryBook(request),
  });
}

/**
 * Preview data for a generated book.
 * Polls every 3 s until status = 'completed' or 'failed'.
 */
export function useGeneratedBookPreview(bookId: string) {
  return useQuery({
    queryKey: ['generatedBookPreview', bookId],
    queryFn: () => storyBookTemplatesService.getGeneratedBookPreview(bookId),
    enabled: !!bookId,
    staleTime: 0,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'completed' || status === 'failed' || status === 'cancelled') {
        return false;
      }
      return 3000; // poll every 3 s while processing / queued
    },
  });
}
