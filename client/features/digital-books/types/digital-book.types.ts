export type DigitalBookType = 'story' | 'coloring';
export type DigitalBookStyle = 'animation' | 'illustration';
export type DigitalBookAgeGroup = '5-9' | '10-14';
export type DigitalBookLanguage = 'english';

export interface DigitalBook {
  id: number;
  bookName: string;
  description: string | null;
  coverImageUrl: string | null;
  coverImagePresignedUrl: string | null;
  totalPages: number | null;
  bookType: DigitalBookType | null;
  theme: string | null;
  style: DigitalBookStyle | null;
  ageGroup: DigitalBookAgeGroup | null;
  language: DigitalBookLanguage | null;
  genreId: number | null;
  genreName: string | null;
  price: number | null;
  rating: number;
  totalRatings: number;
  downloadCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface DigitalBookFilters {
  search?: string;
  bookType?: DigitalBookType;
  genre?: string;
  style?: DigitalBookStyle;
  ageGroup?: DigitalBookAgeGroup;
  language?: DigitalBookLanguage;
}

export interface DigitalBookFilterOptions {
  bookTypes: DigitalBookType[];
  styles: DigitalBookStyle[];
  ageGroups: DigitalBookAgeGroup[];
  languages: DigitalBookLanguage[];
  genres: string[];
}

export interface SendDigitalBookEmailPayload {
  bookId: number;
  email: string;
}
