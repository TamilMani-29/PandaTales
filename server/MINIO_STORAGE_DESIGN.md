# MinIO Object Storage Design for PandaTales

**Storage Solution:** MinIO (S3-Compatible)  
**Bucket Strategy:** Single bucket with organized prefixes  
**CDN:** MinIO built-in (can add CloudFlare later)  
**Date:** March 1, 2026

---

## 📋 Storage Architecture

### Bucket Structure

**Main Bucket:** `pandatales`

```
pandatales/
├── templates/                          # Template assets (static, cacheable)
│   ├── story-books/
│   │   ├── covers/                     # Story book template covers
│   │   │   └── {template_id}.{ext}    # e.g., uuid.jpg, uuid.png
│   │   ├── previews/                   # Preview page images
│   │   │   └── {template_id}/
│   │   │       └── page-{n}.{ext}
│   │   └── samples/                    # Sample pages for showcase
│   │       └── {template_id}/
│   │           └── sample-{n}.{ext}
│   │
│   └── coloring-books/
│       ├── covers/                     # Coloring book template covers
│       │   └── {template_id}.{ext}
│       ├── previews/                   # Preview page images
│       │   └── {template_id}/
│       │       └── page-{n}.{ext}
│       └── samples/                    # Sample coloring pages
│           └── {template_id}/
│               └── sample-{n}.{ext}
│
├── generated/                          # Generated content (user-specific)
│   ├── books/
│   │   ├── story/
│   │   │   ├── pdfs/                   # Generated story book PDFs
│   │   │   │   └── {book_id}.pdf
│   │   │   ├── covers/                 # Generated cover images
│   │   │   │   └── {book_id}.{ext}
│   │   │   └── pages/                  # Individual page images
│   │   │       └── {book_id}/
│   │   │           └── page-{n}.{ext}
│   │   │
│   │   └── coloring/
│   │       ├── pdfs/                   # Generated coloring book PDFs
│   │       │   └── {book_id}.pdf
│   │       ├── covers/                 # Generated cover images
│   │       │   └── {book_id}.{ext}
│   │       └── pages/                  # Individual coloring pages
│   │           └── {book_id}/
│   │               └── page-{n}.{ext}
│   │
│   └── temp/                           # Temporary files (7-day lifecycle)
│       └── {session_id}/
│           └── *.tmp
│
├── users/                              # User-uploaded content
│   ├── avatars/                        # User profile pictures
│   │   └── {user_id}.{ext}
│   │
│   └── uploads/
│       └── photos/                     # Child photos (for photo-to-coloring)
│           └── {user_id}/
│               └── {photo_id}.{ext}
│
└── public/                             # Publicly accessible static content
    ├── assets/                         # App assets (logos, icons)
    │   └── *.{ext}
    └── marketing/                      # Marketing materials
        └── *.{ext}
```

---

## 🔐 Access Control Policies

### Bucket Policies

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadTemplateCovers",
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["s3:GetObject"],
      "Resource": [
        "arn:aws:s3:::pandatales/templates/*/covers/*",
        "arn:aws:s3:::pandatales/templates/*/previews/*",
        "arn:aws:s3:::pandatales/templates/*/samples/*",
        "arn:aws:s3:::pandatales/public/*"
      ]
    },
    {
      "Sid": "AuthenticatedReadGenerated",
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["s3:GetObject"],
      "Resource": [
        "arn:aws:s3:::pandatales/generated/books/*/pdfs/*",
        "arn:aws:s3:::pandatales/generated/books/*/covers/*",
        "arn:aws:s3:::pandatales/generated/books/*/pages/*"
      ],
      "Condition": {
        "StringLike": {
          "aws:Referer": ["https://pandatales.com/*"]
        }
      }
    }
  ]
}
```

---

## 📦 File Naming Conventions

### Templates
- **Covers:** `{template_id}.{ext}` (e.g., `550e8400-e29b-41d4-a716-446655440000.jpg`)
- **Previews:** `{template_id}/page-{number}.{ext}` (e.g., `uuid/page-1.jpg`)
- **Samples:** `{template_id}/sample-{number}.{ext}`

### Generated Books
- **PDFs:** `{book_id}.pdf`
- **Covers:** `{book_id}.{ext}` (jpg, png)
- **Pages:** `{book_id}/page-{number}.{ext}`

### User Content
- **Avatars:** `{user_id}.{ext}` (jpg, png, webp)
- **Photos:** `{user_id}/{photo_id}.{ext}`

---

## 🗃️ File Types & Sizes

| Type | Extension | Max Size | Content-Type |
|------|-----------|----------|--------------|
| **Template Covers** | jpg, png, webp | 2 MB | image/jpeg, image/png, image/webp |
| **Generated PDFs** | pdf | 50 MB | application/pdf |
| **Page Images** | jpg, png | 5 MB | image/jpeg, image/png |
| **User Avatars** | jpg, png, webp | 5 MB | image/jpeg, image/png, image/webp |
| **Child Photos** | jpg, png | 10 MB | image/jpeg, image/png |

---

## ⏱️ Lifecycle Policies

### Temporary Files
```javascript
{
  prefix: "generated/temp/",
  expiration: "7 days",
  action: "delete"
}
```

### Generated Books (Unpurchased)
```javascript
{
  prefix: "generated/books/*/",
  expiration: "30 days",
  condition: "not_purchased",  // Custom logic in app
  action: "delete"
}
```

---

## 🚀 Performance Optimization

### CDN Configuration
- **Caching:** 
  - Templates: 1 year (immutable)
  - Generated content: 1 day
  - User uploads: 1 week
  
### Compression
- Enable gzip for:
  - Text files
  - JSON responses
  - SVG images

### Image Optimization
- Store multiple sizes:
  - `thumbnail` (200x200)
  - `medium` (800x800)
  - `large` (1600x1600)
  - `original` (as uploaded)

---

## 🔒 Security Considerations

### 1. Pre-signed URLs
- **Upload:** Valid for 5 minutes
- **Download:** Valid for 1 hour (generated books)
- **Public:** No expiration (templates)

### 2. File Scanning
- Virus scan all user uploads before storing
- Reject suspicious file types

### 3. Rate Limiting
- Max 10 uploads per minute per user
- Max 100 downloads per hour per IP

### 4. Encryption
- Server-side encryption (SSE-S3)
- TLS 1.3 for all transfers

---

## 📊 Storage Estimates

### Per User (Average)
- Child photos: 5 photos × 5 MB = 25 MB
- Generated books: 3 books × 20 MB = 60 MB
- Avatar: 1 MB
- **Total per active user:** ~86 MB

### Per Template
- Cover image: 1 MB
- Preview images: 5 × 2 MB = 10 MB
- **Total per template:** ~11 MB

### Projected Storage (1 year)
- 10,000 users × 86 MB = 860 GB
- 100 templates × 11 MB = 1.1 GB
- **Total:** ~861 GB ≈ 1 TB

---

## 🛠️ Implementation Checklist

- [x] Design bucket structure
- [x] Define naming conventions
- [x] Set up access policies
- [ ] Implement lifecycle policies
- [ ] Configure CDN
- [ ] Set up backup strategy
- [ ] Implement monitoring
- [ ] Add metrics (storage used, bandwidth)

---

## 📝 Development Setup

### MinIO Console Access
- URL: http://localhost:9001
- Username: `minioadmin`
- Password: `minioadmin123`

### MinIO API Endpoint
- URL: http://localhost:9000
- Region: `us-east-1`

### Test Files
```bash
# Upload test cover
aws s3 cp test-cover.jpg s3://pandatales/templates/story-books/covers/test-uuid.jpg --endpoint-url http://localhost:9000

# Download generated book
aws s3 cp s3://pandatales/generated/books/story/pdfs/book-uuid.pdf ./book.pdf --endpoint-url http://localhost:9000
```

---

## 🔄 Migration from Existing Storage

If migrating from another storage solution:

1. Export existing file inventory
2. Map old paths to new structure
3. Bulk copy with AWS CLI or rclone
4. Verify checksums
5. Update database URLs
6. Switch application to new structure
7. Keep old storage as backup for 30 days
