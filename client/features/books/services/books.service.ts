import { StoryBook, ColoringBookTemplateListItem, GenerateBookRequest, BookPreviewData } from '@/types/book.types';
import { coloringTemplatesService } from '@/features/coloring/services/coloring-templates.service';
import {
  storyBookTemplatesService,
  mapToStoryBook,
  mapTemplateToStoryBook,
} from './story-book-templates.service';
import {
  isMockPreviewId,
  mockGetStoryBook,
  mockGetColoringBook,
} from '@/lib/mock-api/mock-generation.service';

export const booksService = {
  async getAllStoryBooks(): Promise<StoryBook[]> {
    const result = await storyBookTemplatesService.getTemplates({ limit: 100 });
    return result.data.map(mapToStoryBook);
  },

  async getAllColoringBooks(): Promise<ColoringBookTemplateListItem[]> {
    const result = await coloringTemplatesService.getTemplates();
    return result.data;
  },

  async getStoryBookById(id: string): Promise<StoryBook | null> {
    // TODO: Remove mock guard when backend generation is ready.
    if (isMockPreviewId(id)) return mockGetStoryBook(id);
    try {
      const template = await storyBookTemplatesService.getTemplateById(id);
      return mapTemplateToStoryBook(template);
    } catch {
      return null;
    }
  },

  async getColoringBookById(id: string): Promise<ColoringBookTemplateListItem | null> {
    // TODO: Remove mock guard when backend generation is ready.
    if (isMockPreviewId(id)) return mockGetColoringBook(id);
    try {
      return await coloringTemplatesService.getTemplateById(id);
    } catch {
      return null;
    }
  },

  /** Initiate story book generation. Returns { id (generation_id), status }. */
  async generateBook(request: GenerateBookRequest): Promise<{ id: string; status: string }> {
    return storyBookTemplatesService.generateStoryBook(request);
  },

  /** Get preview data (polls via useBooks hook refetchInterval). */
  async getBookPreview(bookId: string): Promise<BookPreviewData> {
    return storyBookTemplatesService.getGeneratedBookPreview(bookId);
  },
};
