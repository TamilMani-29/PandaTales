import apiClient from '@/lib/api/axios';
import { ENDPOINTS } from '@/lib/api/endpoints';
import {
  mockGenerateStoryBook,
  mockGetGeneratedBookPreview,
  isMockPreviewId,
} from '@/lib/mock-api/mock-generation.service';

// TODO: Set to false (and remove the mock guard blocks below) when the backend
//       AI generation pipeline is ready for end-to-end use.
const USE_MOCK_GENERATION = false;
import {
  StoryBook,
  StoryBookTemplate,
  StoryBookTemplateListItem,
  StoryTemplateFilters,
  StoryTemplatesPaginatedResult,
  GenerateBookRequest,
  BookPreviewData,
  AgeGroup,
  BookType,
  ReadingLevel,
} from '@/types/book.types';

// ── Raw API types (snake_case from FastAPI) ───────────────────────────────────

interface ApiStoryBookListItem {
  id: string;
  title: string;
  description: string;
  genre: string;
  age_group: string;
  reading_level: string | null;
  price: number;
  cover_image_url: string;
  total_pages: number;
  tags: string[];
}

interface ApiStoryBookResponse extends ApiStoryBookListItem {
  long_description: string | null;
  book_type: string | null;
  series_id: string | null;
  book_number: number | null;
  story_theme: string | null;
  moral_lesson: string | null;
  preview_images: string[];
  features: string[];
  learning_outcomes: string[];
  chapters: Array<{ number: number; title: string; pages: string }>;
  customization_options: Record<string, unknown>;
  is_published: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface ApiPaginationMetadata {
  page: number;
  limit: number;
  total: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

interface ApiPaginatedResponse<T> {
  success: boolean;
  message: string;
  data: T[];
  pagination: ApiPaginationMetadata;
}

interface ApiSuccessResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

interface ApiBookGenerationResponse {
  generation_id: string;
  status: string;
  estimated_time: number;
  queue_position: number;
}

interface ApiBookPage {
  page_number: number;
  image_url: string;
  text: string | null;
}

interface ApiTemplateInfo {
  title: string;
  genre: string | null;
  theme: string | null;
  age_group: string;
}

interface ApiChildInfo {
  id: string | null;
  name: string;
  age: number;
  gender: string;
}

interface ApiGeneratedBookResponse {
  id: string;
  template_id: string;
  template_type: 'story_book' | 'coloring_book';
  generation_type: string | null;
  selected_theme_name: string | null;
  template: ApiTemplateInfo;
  child: ApiChildInfo;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  is_purchased: boolean;
  cover_image_url: string | null;
  total_pages: number | null;
  preview_pages: ApiBookPage[] | null;
  generated_at: string;
  completed_at: string | null;
  progress: number;
}

// ── Mappers ───────────────────────────────────────────────────────────────────

function capitaliseFirst(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function mapListItem(item: ApiStoryBookListItem): StoryBookTemplateListItem {
  return {
    id: item.id,
    title: item.title,
    description: item.description,
    genre: item.genre,
    ageGroup: item.age_group as AgeGroup,
    readingLevel: item.reading_level as ReadingLevel | null,
    price: item.price,
    coverImageUrl: item.cover_image_url,
    totalPages: item.total_pages,
    tags: item.tags,
  };
}

function mapTemplate(item: ApiStoryBookResponse): StoryBookTemplate {
  return {
    ...mapListItem(item),
    longDescription: item.long_description,
    bookType: item.book_type as BookType | null,
    seriesId: item.series_id,
    bookNumber: item.book_number,
    storyTheme: item.story_theme,
    moralLesson: item.moral_lesson,
    previewImages: item.preview_images,
    features: item.features,
    learningOutcomes: item.learning_outcomes,
    chapters: item.chapters,
    customizationOptions: item.customization_options,
    isPublished: item.is_published,
    isActive: item.is_active,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  };
}

/** Map API list item to the StoryBook shape used by BookCard */
export function mapToStoryBook(item: StoryBookTemplateListItem): StoryBook {
  return {
    id: item.id,
    title: item.title,
    type: 'single' as BookType, // default; overridden by full template
    genre: capitaliseFirst(item.genre),
    ageGroup: item.ageGroup,
    price: item.price,
    description: item.description,
    coverImage: item.coverImageUrl,
    previewImages: [], // list items do not carry preview images
    totalPages: item.totalPages,
    readingLevel: item.readingLevel,
    tags: item.tags,
  };
}

/** Map full template to the StoryBook shape used by create/preview pages */
export function mapTemplateToStoryBook(template: StoryBookTemplate): StoryBook {
  return {
    id: template.id,
    title: template.title,
    type: (template.bookType ?? 'single') as BookType,
    genre: capitaliseFirst(template.genre),
    ageGroup: template.ageGroup,
    price: template.price,
    description: template.description,
    coverImage: template.coverImageUrl,
    previewImages: template.previewImages ?? [],
    totalPages: template.totalPages,
    readingLevel: template.readingLevel,
    tags: template.tags,
  };
}

// ── Service ───────────────────────────────────────────────────────────────────

export const storyBookTemplatesService = {
  /**
   * GET /api/v1/story-books
   * Paginated list of story book templates with optional filters.
   */
  async getTemplates(
    filters: StoryTemplateFilters = {}
  ): Promise<StoryTemplatesPaginatedResult> {
    const params: Record<string, string | number> = {};
    if (filters.genre) params.genre = filters.genre.toLowerCase(); // API expects lowercase
    if (filters.ageGroup) params.age_group = filters.ageGroup;
    if (filters.readingLevel) params.reading_level = filters.readingLevel;
    if (filters.minPrice !== undefined) params.min_price = filters.minPrice;
    if (filters.maxPrice !== undefined) params.max_price = filters.maxPrice;
    if (filters.search) params.search = filters.search;
    if (filters.sortBy) params.sort_by = filters.sortBy;
    if (filters.sortOrder) params.sort_order = filters.sortOrder;
    if (filters.page) params.page = filters.page;
    if (filters.limit) params.limit = filters.limit ?? 50;

    const { data } = await apiClient.get<ApiPaginatedResponse<ApiStoryBookListItem>>(
      ENDPOINTS.storyBooks.getAll,
      { params }
    );

    return {
      data: data.data.map(mapListItem),
      pagination: {
        page: data.pagination.page,
        limit: data.pagination.limit,
        total: data.pagination.total,
        pages: data.pagination.pages,
        hasNext: data.pagination.has_next,
        hasPrev: data.pagination.has_prev,
      },
    };
  },

  /**
   * GET /api/v1/story-books/{id}
   * Full details for a single story book template.
   */
  async getTemplateById(id: string): Promise<StoryBookTemplate> {
    const { data } = await apiClient.get<ApiSuccessResponse<ApiStoryBookResponse>>(
      ENDPOINTS.storyBooks.getById(id)
    );
    return mapTemplate(data.data);
  },

  /**
   * GET /api/v1/story-books/genres/list
   * Distinct genre strings (for filter UI).
   */
  async getGenresList(): Promise<string[]> {
    const { data } = await apiClient.get<ApiSuccessResponse<{ genres: string[] }>>(
      ENDPOINTS.storyBooks.genres
    );
    return data.data.genres;
  },

  /**
   * POST /api/v1/books/generate  (template_type=story_book)
   * Initiate story book generation — returns { id (generation_id), status }.
   */
  async generateStoryBook(
    request: GenerateBookRequest
  ): Promise<{ id: string; status: string }> {
    // TODO: Remove this mock block when backend generation is ready.
    if (USE_MOCK_GENERATION) return mockGenerateStoryBook();

    const formData = new FormData();
    formData.append('template_id', request.templateId);
    formData.append('template_type', 'story_book');
    formData.append('child_name', request.childName);
    formData.append('child_age', String(request.childAge));
    formData.append('child_gender', request.childGender);
    formData.append('parent_email', request.parentEmail);
    if (request.whatsappNumber) {
      formData.append('whatsapp_number', request.whatsappNumber);
    }
    request.photos.forEach((photo) => {
      formData.append('photos', photo);
    });

    const { data } = await apiClient.post<ApiSuccessResponse<ApiBookGenerationResponse>>(
      ENDPOINTS.books.generate,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );

    return {
      id: data.data.generation_id,
      status: data.data.status,
    };
  },

  /**
   * GET /api/v1/books/{id}
   * Get preview data for a generated book (polls until completed).
   */
  async getGeneratedBookPreview(bookId: string): Promise<BookPreviewData> {
    // TODO: Remove this mock block when backend generation is ready.
    if (isMockPreviewId(bookId)) return mockGetGeneratedBookPreview(bookId);

    const { data } = await apiClient.get<ApiSuccessResponse<ApiGeneratedBookResponse>>(
      ENDPOINTS.generatedBooks.getById(bookId)
    );
    const book = data.data;

    return {
      id: book.id,
      status: book.status,
      progress: book.progress,
      previewPages: book.preview_pages?.map((p) => p.image_url) ?? [],
      totalPages: book.total_pages ?? 24,
      childName: book.child.name,
      templateType: book.template_type,
      templateTitle: book.template.title,
      coverImageUrl: book.cover_image_url,
      isPurchased: book.is_purchased,
    };
  },

  /**
   * GET /api/v1/books/{id}/download-pdf
   * Build the PDF on the backend and trigger a browser file download.
   */
  async downloadBookPdf(bookId: string, childName: string): Promise<void> {
    const response = await apiClient.get(ENDPOINTS.books.downloadPdf(bookId), {
      responseType: 'blob',
    });
    const url = URL.createObjectURL(response.data as Blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${childName.replace(/\s+/g, '_')}_storybook.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};
