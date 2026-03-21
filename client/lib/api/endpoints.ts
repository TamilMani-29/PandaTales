export const ENDPOINTS = {
  storyBooks: {
    getAll: '/v1/story-books',
    getById: (id: string) => `/v1/story-books/${id}`,
    genres: '/v1/story-books/genres/list',
    series: (seriesId: string) => `/v1/story-books/series/${seriesId}`,
  },
  coloringBooks: {
    getAll: '/v1/coloring-books',
    getById: (id: string) => `/v1/coloring-books/${id}`,
    themes: '/v1/coloring-books/themes/list',
  },
  generationThemes: {
    getActive: '/v1/themes',
  },
  books: {
    generate: '/v1/books/generate',
    generatePhotoToColoring: '/v1/books/generate/photo-to-coloring',
    generateThemeBased: '/v1/books/generate/theme-based',
    generationStatus: (id: string) => `/v1/books/generate/${id}/status`,
  },
  generatedBooks: {
    getById: (id: string) => `/v1/books/${id}`,
    list: '/v1/books/generated',
  },
  checkout: {
    createOrder: '/v1/checkout/create-order',
    verifyPayment: '/v1/checkout/verify-payment',
    orders: '/v1/checkout/orders',
  },
  user: {
    orders: '/v1/user/orders',
    profile: '/v1/users/me',
  },
  auth: {
    login: '/v1/auth/login',
    logout: '/v1/auth/logout',
    register: '/v1/auth/register',
  },
} as const;
