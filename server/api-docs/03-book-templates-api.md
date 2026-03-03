# Book Templates API

**Base Path:** `/api/v1/templates`  
**Version:** 1.0  
**Authentication:** Optional (public for browsing, required for favorites)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Endpoints](#endpoints)
3. [Data Models](#data-models)
4. [Filtering & Search](#filtering--search)

---

## Overview

The Book Templates API provides access to pre-designed story book and coloring book templates that users can personalize.

### Features
- Browse story book and coloring book templates
- Advanced search and filtering
- Template categories and genres
- Age group categorization
- Series support

---

## Endpoints

### 1. List Story Book Templates

**Endpoint:** `GET /api/v1/templates/story-books`

**Description:** Get paginated list of story book templates with filtering and search.

**Query Parameters:**
- `page` (integer, default: 1): Page number
- `pageSize` (integer, default: 20, max: 100): Items per page
- `search` (string): Search term for title/description
- `ageGroup` (string[]): Filter by age groups ('0-2', '3-5', '6-8', '9-12')
- `genre` (string[]): Filter by genres
- `type` (string): Filter by type ('single', 'series', 'all')
- `priceMin` (number): Minimum price filter
- `priceMax` (number): Maximum price filter
- `sort` (string): Sort field ('title', 'price', 'newest')
- `order` (string): Sort order ('asc', 'desc')

**Example Request:**
```
GET /api/v1/templates/story-books?
  page=1&
  pageSize=20&
  ageGroup=3-5,6-8&
  genre=adventure,fantasy&
  sort=newest&
  order=desc
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "tmpl_sb_001",
        "title": "My First Adventure",
        "description": "A personalized adventure where your child becomes the hero!",
        "type": "single",
        "genre": "adventure",
        "ageGroup": "3-5",
        "price": 24.99,
        "coverImage": "https://cdn.pandatales.com/templates/sb_001_cover.jpg",
        "previewImages": [
          "https://cdn.pandatales.com/templates/sb_001_p1.jpg",
          "https://cdn.pandatales.com/templates/sb_001_p2.jpg"
        ],
        "totalPages": 20,
        "createdAt": "2025-12-01T00:00:00Z"
      },
      {
        "id": "tmpl_sb_002",
        "title": "The Magical Forest Quest",
        "description": "Join your child on a magical journey through an enchanted forest.",
        "type": "single",
        "genre": "fantasy",
        "ageGroup": "6-8",
        "price": 29.99,
        "coverImage": "https://cdn.pandatales.com/templates/sb_002_cover.jpg",
        "previewImages": [
          "https://cdn.pandatales.com/templates/sb_002_p1.jpg"
        ],
        "totalPages": 24,
        "createdAt": "2025-11-15T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalPages": 3,
      "totalItems": 45,
      "hasNext": true,
      "hasPrev": false
    },
    "filters": {
      "availableAgeGroups": ["0-2", "3-5", "6-8", "9-12"],
      "availableGenres": ["adventure", "fantasy", "educational", "bedtime", "superhero"],
      "priceRange": {
        "min": 19.99,
        "max": 34.99
      }
    }
  }
}
```

---

### 2. Get Story Book Template Details

**Endpoint:** `GET /api/v1/templates/story-books/{templateId}`

**Description:** Get detailed information about a specific story book template.

**Path Parameters:**
- `templateId` - Template ID

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "tmpl_sb_001",
    "title": "My First Adventure",
    "description": "A personalized adventure where your child becomes the hero! This engaging story follows your child as they embark on their very first big adventure.",
    "longDescription": "In this beautifully illustrated story...",
    "type": "single",
    "genre": "adventure",
    "ageGroup": "3-5",
    "price": 24.99,
    "coverImage": "https://cdn.pandatales.com/templates/sb_001_cover.jpg",
    "previewImages": [
      "https://cdn.pandatales.com/templates/sb_001_p1.jpg",
      "https://cdn.pandatales.com/templates/sb_001_p2.jpg",
      "https://cdn.pandatales.com/templates/sb_001_p3.jpg"
    ],
    "totalPages": 20,
    "features": [
      "Personalized character with child's name",
      "Include child's photo on every page",
      "Customizable character appearance",
      "Educational learning points"
    ],
    "learningOutcomes": [
      "Builds confidence",
      "Encourages problem-solving",
      "Promotes imagination"
    ],
    "customizationOptions": {
      "namePersonalization": true,
      "photoInclusion": true,
      "characterGender": true,
      "characterAppearance": false
    },
    "tags": ["adventure", "confidence", "first-time", "hero"],
    "createdAt": "2025-12-01T00:00:00Z",
    "updatedAt": "2026-02-10T10:30:00Z"
  }
}
```

**Errors:**
- `404` - Template not found

---

### 3. List Coloring Book Templates

**Endpoint:** `GET /api/v1/templates/coloring-books`

**Description:** Get paginated list of coloring book templates.

**Query Parameters:**
Same as story books except:
- No `type` parameter (all coloring books are single)

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "tmpl_cb_001",
        "title": "Magical Creatures",
        "description": "Beautiful coloring pages featuring mythical creatures",
        "genre": "fantasy",
        "ageGroup": "6-8",
        "price": 14.99,
        "coverImage": "https://cdn.pandatales.com/templates/cb_001_cover.jpg",
        "previewImages": [
          "https://cdn.pandatales.com/templates/cb_001_p1.jpg"
        ],
        "totalPages": 32,
        "createdAt": "2025-11-20T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalPages": 2,
      "totalItems": 30,
      "hasNext": true,
      "hasPrev": false
    }
  }
}
```

---

### 4. Get Coloring Book Template Details

**Endpoint:** `GET /api/v1/templates/coloring-books/{templateId}`

**Description:** Get detailed information about a coloring book template.

**Response:** Similar structure to story book details with coloring-specific fields.

---

### 5. Search Templates

**Endpoint:** `GET /api/v1/templates/search`

**Description:** Search across both story books and coloring books.

**Query Parameters:**
- `q` (string, required): Search query
- `category` (string): 'story-books', 'coloring-books', 'all' (default: 'all')
- `page`, `pageSize`, filters...

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "storyBooks": {
      "items": [...],
      "count": 12
    },
    "coloringBooks": {
      "items": [...],
      "count": 5
    },
    "totalResults": 17
  }
}
```

---

### 6. Get New Templates

**Endpoint:** `GET /api/v1/templates/new`

**Description:** Get recently added templates.

**Query Parameters:**
- `category` (string): 'story-books', 'coloring-books', 'all'
- `limit` (integer, default: 10, max: 50)
- `days` (integer, default: 30): Within last N days

**Response:** `200 OK`

---

### 7. Get Template Categories

**Endpoint:** `GET /api/v1/templates/categories`

**Description:** Get all available categories, genres, and age groups.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "ageGroups": [
      {
        "value": "0-2",
        "label": "Infant (0-2 years)",
        "count": 12
      },
      {
        "value": "3-5",
        "label": "Preschool (3-5 years)",
        "count": 45
      },
      {
        "value": "6-8",
        "label": "Early Elementary (6-8 years)",
        "count": 38
      },
      {
        "value": "9-12",
        "label": "Elementary (9-12 years)",
        "count": 25
      }
    ],
    "genres": {
      "storyBooks": [
        {
          "value": "adventure",
          "label": "Adventure",
          "count": 28,
          "icon": "🗺️"
        },
        {
          "value": "fantasy",
          "label": "Fantasy",
          "count": 22,
          "icon": "✨"
        },
        {
          "value": "educational",
          "label": "Educational",
          "count": 18,
          "icon": "📚"
        },
        {
          "value": "bedtime",
          "label": "Bedtime Stories",
          "count": 15,
          "icon": "🌙"
        },
        {
          "value": "superhero",
          "label": "Superhero",
          "count": 12,
          "icon": "🦸"
        }
      ],
      "coloringBooks": [
        {
          "value": "animals",
          "label": "Animals",
          "count": 15,
          "icon": "🐾"
        },
        {
          "value": "fantasy",
          "label": "Fantasy",
          "count": 12,
          "icon": "✨"
        },
        {
          "value": "nature",
          "label": "Nature",
          "count": 8,
          "icon": "🌸"
        }
      ]
    }
  }
}
```

---

### 8. Get Series Templates

**Endpoint:** `GET /api/v1/templates/series/{seriesId}`

**Description:** Get all books in a series.

**Path Parameters:**
- `seriesId` - Series identifier

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "seriesId": "series_superkid",
    "seriesName": "Super Kid Adventures",
    "description": "Follow Super Kid through amazing adventures!",
    "totalBooks": 5,
    "books": [
      {
        "id": "tmpl_sb_010",
        "title": "Super Kid Saves the Day - Book 1",
        "bookNumber": 1,
        "coverImage": "...",
        "price": 24.99
      },
      {
        "id": "tmpl_sb_011",
        "title": "Super Kid's Space Mission - Book 2",
        "bookNumber": 2,
        "coverImage": "...",
        "price": 24.99
      }
    ]
  }
}
```

---

## Data Models

### Story Book Template Model
```python
class StoryBookTemplate:
    id: str
    title: str
    description: str
    long_description: Optional[str]
    type: str  # 'single', 'series'
    series_id: Optional[str]
    book_number: Optional[int]
    genre: str
    age_group: str
    price: float
    cover_image: str
    preview_images: List[str]
    total_pages: int
    features: List[str]
    learning_outcomes: Optional[List[str]]
    customization_options: dict
    total_generated: int
    is_popular: bool
    tags: List[str]
    created_at: datetime
    updated_at: datetime
```

### Coloring Book Template Model
```python
class ColoringBookTemplate:
    id: str
    title: str
    description: str
    genre: str
    age_group: str
    price: float
    cover_image: str
    preview_images: List[str]
    total_pages: int
    is_popular: bool
    tags: List[str]
    created_at: datetime
    updated_at: datetime
```

---

## Filtering & Search

### Search Algorithm Priority

1. **Exact title match** (highest priority)
2. **Title contains search term**
3. **Description contains search term**
4. **Tags match**
5. **Genre match** (lowest priority)

### Filter Combinations

All filters can be combined:
- Multiple age groups: OR logic
- Multiple genres: OR logic
- Price range: AND logic with other filters
- Search term: AND logic with filters

### Sort Options

- `title` - Alphabetical by title
- `price` - By price (low to high / high to low)
- `newest` - By creation date
- `rating` - By average rating

---

## Performance Optimization

### Caching Strategy

- Template list: 1 hour cache
- Category data: 6 hours cache
- Template details: 30 minutes cache
- Search results: 15 minutes cache per unique query

### Pagination

- Default page size: 20
- Maximum page size: 100
- Cursor-based pagination for large datasets

---

## Testing

### Test Cases

1. **Listing & Pagination**
   - ✅ Get first page
   - ✅ Navigate pages
   - ✅ Page size limits

2. **Filtering**
   - ✅ Age group filter
   - ✅ Genre filter
   - ✅ Price range filter
   - ✅ Combined filters

3. **Search**
   - ✅ Exact match
   - ✅ Partial match
   - ✅ No results
   - ✅ Search with filters

4. **Series**
   - ✅ Get series templates
   - ✅ Navigate series books

## Seed Data

### Story Book Templates (10)

1. **My First Adventure** (tmpl_sb_001)
   - Type: single
   - Genre: adventure
   - Age: 3-5
   - Price: $24.99

2. **The Magical Forest Quest** (tmpl_sb_002)
   - Type: single
   - Genre: fantasy
   - Age: 6-8
   - Price: $29.99

3-10. (Series and other templates...)

### Coloring Book Templates (10)

Similar seed data structure for coloring books.
