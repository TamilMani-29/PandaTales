import apiClient from '@/lib/api/axios';
import { ENDPOINTS } from '@/lib/api/endpoints';
import {
  DigitalBook,
  DigitalBookFilterOptions,
  DigitalBookFilters,
  SendDigitalBookEmailPayload,
} from '@/features/digital-books/types/digital-book.types';

interface ApiSuccessResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

interface ApiDigitalBook {
  id: number;
  book_name: string;
  description: string | null;
  cover_image_url: string | null;
  cover_image_presigned_url: string | null;
  total_pages: number | null;
  book_type: 'story' | 'coloring' | null;
  theme: string | null;
  style: 'animation' | 'illustration' | null;
  age_group: '5-9' | '10-14' | null;
  language: 'english' | null;
  genre_id: number | null;
  genre_name: string | null;
  price: number | null;
  rating: number;
  total_ratings: number;
  download_count: number;
  created_at: string;
  updated_at: string;
}

interface ApiDigitalBookFilterOptions {
  book_types: Array<'story' | 'coloring'>;
  styles: Array<'animation' | 'illustration'>;
  age_groups: Array<'5-9' | '10-14'>;
  languages: Array<'english'>;
  genres: string[];
}

function mapDigitalBook(item: ApiDigitalBook): DigitalBook {
  return {
    id: item.id,
    bookName: item.book_name,
    description: item.description,
    coverImageUrl: item.cover_image_url,
    coverImagePresignedUrl: item.cover_image_presigned_url,
    totalPages: item.total_pages,
    bookType: item.book_type,
    theme: item.theme,
    style: item.style,
    ageGroup: item.age_group,
    language: item.language,
    genreId: item.genre_id,
    genreName: item.genre_name,
    price: item.price,
    rating: item.rating,
    totalRatings: item.total_ratings,
    downloadCount: item.download_count,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  };
}

function mapFilterOptions(options: ApiDigitalBookFilterOptions): DigitalBookFilterOptions {
  return {
    bookTypes: options.book_types,
    styles: options.styles,
    ageGroups: options.age_groups,
    languages: options.languages,
    genres: options.genres,
  };
}

export const digitalBooksService = {
  async getBooks(filters: DigitalBookFilters = {}): Promise<DigitalBook[]> {
    const params: Record<string, string> = {};

    if (filters.search) params.search = filters.search;
    if (filters.bookType) params.book_type = filters.bookType;
    if (filters.genre) params.genre = filters.genre;
    if (filters.style) params.style = filters.style;
    if (filters.ageGroup) params.age_group = filters.ageGroup;
    if (filters.language) params.language = filters.language;

    const { data } = await apiClient.get<ApiSuccessResponse<ApiDigitalBook[]>>(
      ENDPOINTS.digitalBooks.list,
      { params }
    );

    return data.data.map(mapDigitalBook);
  },

  async getBookById(id: number): Promise<DigitalBook> {
    const { data } = await apiClient.get<ApiSuccessResponse<ApiDigitalBook>>(
      ENDPOINTS.digitalBooks.details(id)
    );

    return mapDigitalBook(data.data);
  },

  async getFilterOptions(): Promise<DigitalBookFilterOptions> {
    const { data } = await apiClient.get<ApiSuccessResponse<ApiDigitalBookFilterOptions>>(
      ENDPOINTS.digitalBooks.filterOptions
    );

    return mapFilterOptions(data.data);
  },

  async sendBookToEmail(payload: SendDigitalBookEmailPayload): Promise<{ bookId: number; email: string }> {
    const { data } = await apiClient.post<ApiSuccessResponse<{ book_id: number; email: string }>>(
      ENDPOINTS.digitalBooks.sendPdfEmail,
      {
        book_id: payload.bookId,
        email: payload.email,
      }
    );

    return {
      bookId: data.data.book_id,
      email: data.data.email,
    };
  },
};
