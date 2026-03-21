/**
 * MOCK GENERATION SERVICE
 *
 * TODO: Delete this file (and remove all references to it in services) when the
 *       backend AI generation pipeline is ready and end-to-end tested.
 *
 * How it works:
 *  1. Each service function that calls the real generation API has a guard at the
 *     top:  `if (USE_MOCK_GENERATION) return <mockFn>(...)`.
 *  2. The flag `USE_MOCK_GENERATION` lives at the top of the respective service file.
 *  3. To switch back to the real API set  USE_MOCK_GENERATION = false  in:
 *       - client/features/books/services/story-book-templates.service.ts
 *       - client/features/coloring/services/coloring-templates.service.ts
 *     That's the only change needed — the real implementation is already there,
 *     untouched, just below the mock guard.
 *
 * Preview IDs:
 *  Mock generation always returns one of two stable IDs so the preview page can
 *  identify them and return mocked completed data without hitting the backend.
 *    "mock-story-preview"    → story_book
 *    "mock-coloring-preview" → coloring_book
 */

import type { BookPreviewData, BookGenerationResult, StoryBook, ColoringBookTemplateListItem } from '@/types/book.types';

// ── Stable IDs returned by mock generation ───────────────────────────────────

export const MOCK_PREVIEW_ID_STORY = 'mock-story-preview';
export const MOCK_PREVIEW_ID_COLORING = 'mock-coloring-preview';

/** Returns true for any ID that was produced by mock generation. */
export function isMockPreviewId(bookId: string): boolean {
  return bookId === MOCK_PREVIEW_ID_STORY || bookId === MOCK_PREVIEW_ID_COLORING;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Sample page images (children's illustration/book style, from Pexels CDN)
const SAMPLE_STORY_PAGES: string[] = [
  'https://images.pexels.com/photos/4230630/pexels-photo-4230630.jpeg?auto=compress&cs=tinysrgb&w=600',
  'https://images.pexels.com/photos/3293148/pexels-photo-3293148.jpeg?auto=compress&cs=tinysrgb&w=600',
  'https://images.pexels.com/photos/1148998/pexels-photo-1148998.jpeg?auto=compress&cs=tinysrgb&w=600',
];

const SAMPLE_COLORING_PAGES: string[] = [
  'https://images.pexels.com/photos/159866/books-book-pages-read-literature-159866.jpeg?auto=compress&cs=tinysrgb&w=600',
  'https://images.pexels.com/photos/207601/pexels-photo-207601.jpeg?auto=compress&cs=tinysrgb&w=600',
  'https://images.pexels.com/photos/1647962/pexels-photo-1647962.jpeg?auto=compress&cs=tinysrgb&w=600',
];

// ── Mock book template data ──────────────────────────────────────────────────

/**
 * Returns a mock StoryBook for the checkout/preview pages when a mock ID is used.
 * Used in getStoryBookById guard inside books.service.ts.
 *
 * TODO: Remove when real backend generation is wired up.
 */
export function mockGetStoryBook(bookId: string): StoryBook {
  const isStory = bookId === MOCK_PREVIEW_ID_STORY;
  const pages = isStory ? SAMPLE_STORY_PAGES : SAMPLE_COLORING_PAGES;
  return {
    id: bookId,
    title: isStory ? 'The Magical Adventure' : 'Rainbow Coloring Adventure',
    type: 'single',
    genre: 'Fantasy',
    ageGroup: '3-5',
    price: 49900,
    description: 'A personalised book featuring your child as the hero.',
    coverImage: pages[0],
    previewImages: pages,
    totalPages: 24,
    readingLevel: null,
    tags: ['personalised'],
  };
}

/**
 * Returns a mock ColoringBookTemplateListItem for the checkout/preview pages.
 * Used in getColoringBookById guard inside books.service.ts.
 *
 * TODO: Remove when real backend generation is wired up.
 */
export function mockGetColoringBook(bookId: string): ColoringBookTemplateListItem {
  const pages = SAMPLE_COLORING_PAGES;
  return {
    id: bookId,
    title: 'Rainbow Coloring Adventure',
    description: 'A personalised coloring book with fun scenes for your child.',
    theme: 'fantasy',
    ageGroup: '3-5',
    price: 49900,
    coverImageUrl: pages[0],
    totalPages: 24,
    tags: ['personalised'],
  };
}

// ── Mock generation functions ─────────────────────────────────────────────────

/**
 * Simulates story book generation (POST /api/v1/books/generate).
 * Returns after a short artificial delay with a stable mock generation ID.
 *
 * TODO: Replace call-site with the real storyBookTemplatesService.generateStoryBook()
 *       by setting USE_MOCK_GENERATION = false in story-book-templates.service.ts.
 */
export async function mockGenerateStoryBook(): Promise<{ id: string; status: string }> {
  await delay(1500);
  return { id: MOCK_PREVIEW_ID_STORY, status: 'queued' };
}

/**
 * Simulates coloring book generation
 * (POST /api/v1/books/generate/theme-based  or  /generate/photo-to-coloring).
 * Returns after a short artificial delay with a stable mock generation ID.
 *
 * TODO: Replace call-site with the real coloringTemplatesService.generateThemeBased()
 *       / generatePhotoColoring() by setting USE_MOCK_GENERATION = false in
 *       coloring-templates.service.ts.
 */
export async function mockGenerateColoringBook(): Promise<BookGenerationResult> {
  await delay(1500);
  return { id: MOCK_PREVIEW_ID_COLORING, status: 'queued' };
}

// ── Mock payment ─────────────────────────────────────────────────────────────

/**
 * Simulates the full payment flow (createOrder → Razorpay modal → verifyPayment).
 * Returns after a short delay so the UI spinner appears natural.
 *
 * TODO: Remove this function and the USE_MOCK_PAYMENT guard in
 *       client/app/checkout/[bookId]/page.tsx when Razorpay keys are ready.
 *       The real live Razorpay flow is preserved in handleCheckout, just below
 *       the mock guard block.
 */
export async function mockProcessPayment(
  _format: 'digital' | 'softcover' | 'hardcover'
): Promise<void> {
  await delay(1800);
}

// ── Mock preview ─────────────────────────────────────────────────────────────

/**
 * Simulates GET /api/v1/books/{id} — immediately returns a completed book.
 * Automatically picks story/coloring sample data based on the mock ID.
 *
 * TODO: Remove the isMockPreviewId() guard in getGeneratedBookPreview() in
 *       story-book-templates.service.ts once backend generation is ready.
 */
export function mockGetGeneratedBookPreview(bookId: string): BookPreviewData {
  const isStory = bookId === MOCK_PREVIEW_ID_STORY;
  const pages = isStory ? SAMPLE_STORY_PAGES : SAMPLE_COLORING_PAGES;

  return {
    id: bookId,
    status: 'completed',
    progress: 100,
    templateType: isStory ? 'story_book' : 'coloring_book',
    templateTitle: isStory ? 'The Magical Adventure' : 'Rainbow Coloring Adventure',
    childName: 'Your Child',
    coverImageUrl: pages[0],
    previewPages: pages,
    totalPages: 24,
    isPurchased: false,
  };
}
