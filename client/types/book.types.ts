export type BookType = 'single' | 'series';

export type Genre =
  | 'Adventure'
  | 'Fantasy'
  | 'Superhero'
  | 'Animals'
  | 'Space'
  | 'Detective'
  | 'Educational'
  | 'Nature';

export type AgeGroup = '0-2' | '3-5' | '6-8' | '9-12';

export type ColoringBookMode = 'photo' | 'theme';

// ─────────────────────────────────────────────────────────────────────────────
// Coloring Book Template API types
// Maps to backend ColoringBookTemplateListItem / ColoringBookTemplateResponse
// ─────────────────────────────────────────────────────────────────────────────

export interface ColoringBookTemplateListItem {
  id: string;
  title: string;
  description: string;
  theme: string;
  ageGroup: AgeGroup;
  price: number;
  coverImageUrl: string;
  totalPages: number;
  tags: string[];
}

export interface ColoringBookTemplate extends ColoringBookTemplateListItem {
  longDescription: string | null;
  previewImages: string[];
  samplePages: string[];
  pageTypes: string[];
  customizationOptions: Record<string, unknown>;
  isPublished: boolean;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ColoringTemplateFilters {
  theme?: string;
  ageGroup?: AgeGroup;
  minPrice?: number;
  maxPrice?: number;
  search?: string;
  sortBy?: 'title' | 'price' | 'created_at';
  sortOrder?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  pages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface ColoringTemplatesPaginatedResult {
  data: ColoringBookTemplateListItem[];
  pagination: PaginationMeta;
}

// ─────────────────────────────────────────────────────────────────────────────
// Generation themes – returned by GET /api/v1/themes
// ─────────────────────────────────────────────────────────────────────────────

export interface PublicTheme {
  id: string;
  name: string;
  displayName: string;
  description: string | null;
  iconUrl: string | null;
  previewImageUrl: string | null;
  category: string | null;
  tags: string[] | null;
  isPremium: boolean;
  isDefault: boolean;
  minPhotos: number;
  maxPhotos: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// Form submission payload types (used by create flow components)
// ─────────────────────────────────────────────────────────────────────────────

export interface ThemeBasedSubmitData {
  themeConfigId: string;
  numPages: number;
  coloringStyle: 'simple' | 'detailed' | 'mandala' | 'cartoon';
  childName: string;
  childAge: number;
  parentEmail: string;
  photos: File[];
}

export interface PhotoColoringSubmitData {
  childName: string;
  childAge: number;
  parentEmail: string;
  photos: File[];
}

export interface BookGenerationResult {
  id: string;
  status: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Story book types (used for the story books module)
// ─────────────────────────────────────────────────────────────────────────────

export interface StoryBook {
  id: string;
  title: string;
  type: BookType;
  genre: Genre;
  ageGroup: AgeGroup;
  price: number;
  description: string;
  coverImage: string;
  totalPages: number;
}

export interface GenerateBookRequest {
  templateId: string;
  childName: string;
  age: number;
  gender: string;
  parentEmail: string;
  photos: File[];
}

export interface GeneratedBook extends StoryBook {
  childName: string;
  previewPages: string[];
  fullPages: string[];
  isPurchased: boolean;
}

export interface BookFilters {
  search?: string;
  ageGroup?: AgeGroup;
  genre?: Genre;
  type?: BookType;
  minPrice?: number;
  maxPrice?: number;
}

export type SortOption = 'title' | 'price-asc' | 'price-desc' | 'newest';
