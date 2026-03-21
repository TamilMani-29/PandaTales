import { StoryBook, ColoringBookTemplateListItem, GenerateBookRequest, GeneratedBook } from '@/types/book.types';
import booksData from '@/lib/mock-api/books.json';
import { coloringTemplatesService } from '@/features/coloring/services/coloring-templates.service';

const delay = (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms));

export const booksService = {
  async getAllStoryBooks(): Promise<StoryBook[]> {
    await delay();
    return booksData as StoryBook[];
  },

  async getAllColoringBooks(): Promise<ColoringBookTemplateListItem[]> {
    const result = await coloringTemplatesService.getTemplates();
    return result.data;
  },

  async getStoryBookById(id: string): Promise<StoryBook | null> {
    await delay();
    const book = booksData.find(b => b.id === id);
    return book ? (book as StoryBook) : null;
  },

  async getColoringBookById(id: string): Promise<ColoringBookTemplateListItem | null> {
    try {
      return await coloringTemplatesService.getTemplateById(id);
    } catch {
      return null;
    }
  },

  async generateBook(request: GenerateBookRequest): Promise<GeneratedBook> {
    await delay(2000);

    const template = booksData.find(b => b.id === request.templateId);
    if (!template) {
      throw new Error('Template not found');
    }

    return {
      ...template,
      childName: request.childName,
      previewPages: [
        'https://images.pexels.com/photos/1148998/pexels-photo-1148998.jpeg?auto=compress&cs=tinysrgb&w=800',
        'https://images.pexels.com/photos/256417/pexels-photo-256417.jpeg?auto=compress&cs=tinysrgb&w=800'
      ],
      fullPages: Array(template.totalPages).fill('').map((_, i) =>
        `https://images.pexels.com/photos/${1148998 + i}/page-${i + 1}.jpeg`
      ),
      isPurchased: false,
    } as GeneratedBook;
  },

  async getBookPreview(bookId: string): Promise<{ previewPages: string[]; totalPages: number }> {
    await delay();
    return {
      previewPages: [
        'https://images.pexels.com/photos/1148998/pexels-photo-1148998.jpeg?auto=compress&cs=tinysrgb&w=800',
        'https://images.pexels.com/photos/256417/pexels-photo-256417.jpeg?auto=compress&cs=tinysrgb&w=800'
      ],
      totalPages: 24
    };
  },
};
