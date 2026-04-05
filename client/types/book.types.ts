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

export type ReadingLevel = 'beginner' | 'intermediate' | 'advanced';

// Type alias used by BookCard component
export type ColoringBook = ColoringBookTemplateListItem;

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
  whatsappNumber?: string;
  photos: File[];
}

export interface PhotoColoringSubmitData {
  childName: string;
  childAge: number;
  parentEmail: string;
  whatsappNumber?: string;
  photos: File[];
}

export interface BookGenerationResult {
  id: string;
  status: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Story book types (used for the story books module)
// ─────────────────────────────────────────────────────────────────────────────

/** Frontend display shape — used by BookCard, create page, client-side filters */
export interface StoryBook {
  id: string;
  title: string;
  /** 'single' | 'series' — mapped from API's book_type */
  type: BookType;
  /** Capitalised genre string e.g. 'Adventure', 'Fantasy' */
  genre: string;
  ageGroup: AgeGroup;
  price: number;
  description: string;
  /** Mapped from API's cover_image_url */
  coverImage: string;
  /** Preview images for the carousel (up to 5 including cover) */
  previewImages: string[];
  totalPages: number;
  readingLevel?: ReadingLevel | null;
  tags?: string[];
}

/** API-aligned list item returned by GET /v1/story-books */
export interface StoryBookTemplateListItem {
  id: string;
  title: string;
  description: string;
  genre: string;
  ageGroup: AgeGroup;
  readingLevel: ReadingLevel | null;
  price: number;
  coverImageUrl: string;
  totalPages: number;
  tags: string[];
}

/** Full template detail returned by GET /v1/story-books/{id} */
export interface StoryBookTemplate extends StoryBookTemplateListItem {
  longDescription: string | null;
  bookType: BookType | null;
  seriesId: string | null;
  bookNumber: number | null;
  storyTheme: string | null;
  moralLesson: string | null;
  previewImages: string[];
  features: string[];
  learningOutcomes: string[];
  chapters: Array<{ number: number; title: string; pages: string }>;
  customizationOptions: Record<string, unknown>;
  isPublished: boolean;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface StoryTemplateFilters {
  genre?: string;
  ageGroup?: AgeGroup;
  readingLevel?: ReadingLevel;
  minPrice?: number;
  maxPrice?: number;
  search?: string;
  sortBy?: 'title' | 'price' | 'created_at';
  sortOrder?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export interface StoryTemplatesPaginatedResult {
  data: StoryBookTemplateListItem[];
  pagination: PaginationMeta;
}

export interface GenerateBookRequest {
  templateId: string;
  childName: string;
  childAge: number;
  childGender: 'male' | 'female' | 'other';
  parentEmail: string;
  whatsappNumber?: string;
  photos: File[];
}

export interface GeneratedBook extends StoryBook {
  childName: string;
  previewPages: string[];
  fullPages: string[];
  isPurchased: boolean;
}

/** Preview data returned by GET /v1/books/{id} */
export interface BookPreviewData {
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  previewPages: string[];
  totalPages: number;
  childName: string;
  templateType: 'story_book' | 'coloring_book';
  templateTitle: string;
  coverImageUrl: string | null;
  isPurchased: boolean;
}

export interface BookFilters {
  search?: string;
  ageGroup?: AgeGroup[];
  genre?: Genre[];
  type?: BookType[];
  minPrice?: number;
  maxPrice?: number;
}

export type SortOption = 'title' | 'price-asc' | 'price-desc' | 'newest';
