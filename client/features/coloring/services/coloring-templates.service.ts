import apiClient from '@/lib/api/axios';
import { ENDPOINTS } from '@/lib/api/endpoints';
import {
  ColoringBookTemplate,
  ColoringBookTemplateListItem,
  ColoringTemplateFilters,
  ColoringTemplatesPaginatedResult,
  PublicTheme,
  ThemeBasedSubmitData,
  PhotoColoringSubmitData,
  BookGenerationResult,
} from '@/types/book.types';

// ── Raw API types (snake_case matching FastAPI responses) ─────────────────────

interface ApiColoringBookTemplateListItem {
  id: string;
  title: string;
  description: string;
  theme: string;
  age_group: string;
  price: number;
  cover_image_url: string;
  total_pages: number;
  tags: string[];
}

interface ApiColoringBookTemplateResponse extends ApiColoringBookTemplateListItem {
  long_description: string | null;
  preview_images: string[];
  sample_pages: string[];
  page_types: string[];
  customization_options: Record<string, unknown>;
  is_published: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface ApiPublicThemeItem {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
  icon_url: string | null;
  preview_image_url: string | null;
  category: string | null;
  tags: string[] | null;
  is_premium: boolean;
  is_default: boolean;
  min_photos: number;
  max_photos: number;
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

interface ApiGenerationResult {
  id: string;
  status: string;
}

// ── Mappers ──────────────────────────────────────────────────────────────────

function mapTemplateListItem(
  item: ApiColoringBookTemplateListItem
): ColoringBookTemplateListItem {
  return {
    id: item.id,
    title: item.title,
    description: item.description,
    theme: item.theme,
    ageGroup: item.age_group as ColoringBookTemplateListItem['ageGroup'],
    price: item.price,
    coverImageUrl: item.cover_image_url,
    totalPages: item.total_pages,
    tags: item.tags,
  };
}

function mapTemplate(item: ApiColoringBookTemplateResponse): ColoringBookTemplate {
  return {
    ...mapTemplateListItem(item),
    longDescription: item.long_description,
    previewImages: item.preview_images,
    samplePages: item.sample_pages,
    pageTypes: item.page_types,
    customizationOptions: item.customization_options,
    isPublished: item.is_published,
    isActive: item.is_active,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  };
}

function mapPublicTheme(theme: ApiPublicThemeItem): PublicTheme {
  return {
    id: theme.id,
    name: theme.name,
    displayName: theme.display_name,
    description: theme.description,
    iconUrl: theme.icon_url,
    previewImageUrl: theme.preview_image_url,
    category: theme.category,
    tags: theme.tags,
    isPremium: theme.is_premium,
    isDefault: theme.is_default,
    minPhotos: theme.min_photos,
    maxPhotos: theme.max_photos,
  };
}

// ── Service ──────────────────────────────────────────────────────────────────

export const coloringTemplatesService = {
  /**
   * GET /api/v1/coloring-books
   * Paginated list of coloring book templates with optional filters.
   */
  async getTemplates(
    filters: ColoringTemplateFilters = {}
  ): Promise<ColoringTemplatesPaginatedResult> {
    const params: Record<string, string | number> = {};
    if (filters.theme) params.theme = filters.theme;
    if (filters.ageGroup) params.age_group = filters.ageGroup;
    if (filters.minPrice !== undefined) params.min_price = filters.minPrice;
    if (filters.maxPrice !== undefined) params.max_price = filters.maxPrice;
    if (filters.search) params.search = filters.search;
    if (filters.sortBy) params.sort_by = filters.sortBy;
    if (filters.sortOrder) params.sort_order = filters.sortOrder;
    if (filters.page) params.page = filters.page;
    if (filters.limit) params.limit = filters.limit;

    const { data } = await apiClient.get<
      ApiPaginatedResponse<ApiColoringBookTemplateListItem>
    >(ENDPOINTS.coloringBooks.getAll, { params });

    return {
      data: data.data.map(mapTemplateListItem),
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
   * GET /api/v1/coloring-books/{id}
   * Full details for a single template.
   */
  async getTemplateById(id: string): Promise<ColoringBookTemplate> {
    const { data } = await apiClient.get<
      ApiSuccessResponse<ApiColoringBookTemplateResponse>
    >(ENDPOINTS.coloringBooks.getById(id));
    return mapTemplate(data.data);
  },

  /**
   * GET /api/v1/coloring-books/themes/list
   * Distinct theme strings used by existing templates (for filter UI).
   */
  async getThemesList(): Promise<string[]> {
    const { data } = await apiClient.get<ApiSuccessResponse<{ themes: string[] }>>(
      ENDPOINTS.coloringBooks.themes
    );
    return data.data.themes;
  },

  /**
   * GET /api/v1/themes
   * Active generation themes (for theme-based coloring book creation).
   */
  async getActiveThemes(): Promise<PublicTheme[]> {
    const { data } = await apiClient.get<ApiPublicThemeItem[]>(
      ENDPOINTS.generationThemes.getActive
    );
    return data.map(mapPublicTheme);
  },

  /**
   * POST /api/v1/books/generate/theme-based
   * Start a theme-based coloring book generation job.
   */
  async generateThemeBased(
    request: ThemeBasedSubmitData
  ): Promise<BookGenerationResult> {
    const formData = new FormData();
    formData.append('theme_config_id', request.themeConfigId);
    formData.append('num_pages', String(request.numPages));
    formData.append('coloring_style', request.coloringStyle);
    if (request.childName) formData.append('child_name', request.childName);
    if (request.childAge !== undefined)
      formData.append('child_age', String(request.childAge));
    if (request.parentEmail) formData.append('parent_email', request.parentEmail);
    request.photos.forEach((photo) => formData.append('photos', photo));

    const { data } = await apiClient.post<ApiSuccessResponse<ApiGenerationResult>>(
      ENDPOINTS.books.generateThemeBased,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return { id: data.data.id, status: data.data.status };
  },

  /**
   * POST /api/v1/books/generate/photo-to-coloring
   * Convert uploaded photos directly to coloring pages.
   */
  async generatePhotoColoring(
    request: PhotoColoringSubmitData
  ): Promise<BookGenerationResult> {
    const formData = new FormData();
    if (request.childName) formData.append('child_name', request.childName);
    if (request.childAge !== undefined)
      formData.append('child_age', String(request.childAge));
    if (request.parentEmail) formData.append('parent_email', request.parentEmail);
    request.photos.forEach((photo) => formData.append('photos', photo));

    const { data } = await apiClient.post<ApiSuccessResponse<ApiGenerationResult>>(
      ENDPOINTS.books.generatePhotoToColoring,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return { id: data.data.id, status: data.data.status };
  },
};
