# Story Bloom - Database Schema Design

**Database:** PostgreSQL 15+  
**ORM:** SQLAlchemy 2.0 (Async)  
**Migration Tool:** Alembic  
**Version:** 1.0  
**Last Updated:** February 14, 2026

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Database Architecture](#database-architecture)
3. [Table Schemas](#table-schemas)
4. [Relationships & ERD](#relationships--erd)
5. [Indexes](#indexes)
6. [Constraints](#constraints)
7. [Views](#views)
8. [Migration Strategy](#migration-strategy)

---

## Overview

The Story Bloom database is designed to support a personalized children's book platform with the following key features:

- User authentication and profiles
- Book template catalog
- AI-powered book generation
- E-commerce (cart, orders, payments)
- Digital content delivery

### Design Principles

- **Normalization**: 3rd Normal Form (3NF)
- **Soft Deletes**: Use `is_active` flags instead of hard deletes
- **Timestamps**: All tables have `created_at` and `updated_at`
- **UUIDs**: Use UUID for primary keys for better distribution
- **Audit Trail**: Track important state changes
- **Performance**: Strategic indexing for common queries

---

## Database Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Story Bloom Database                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐         ┌──────────────┐             │
│  │ User Mgmt    │         │  Templates   │             │
│  ├──────────────┤         ├──────────────┤             │
│  │ users        │         │ book_        │             │
│  │ child_       │         │   templates  │             │
│  │   profiles   │         │ template_    │             │
│  │ addresses    │         │   categories │             │
│  └──────────────┘         └──────────────┘             │
│                                                           │
│  ┌──────────────┐         ┌──────────────┐             │
│  │ Generation   │         │  Commerce    │             │
│  ├──────────────┤         ├──────────────┤             │
│  │ generation_  │         │ carts        │             │
│  │   requests   │         │ cart_items   │             │
│  │ generated_   │         │ orders       │             │
│  │   books      │         │ order_items  │             │
│  │ book_pages   │         └──────────────┘             │
│  └──────────────┘                                        │
│                                                           │
│  ┌──────────────┐         ┌──────────────┐             │
│  │  Payments    │         │  Analytics   │             │
│  ├──────────────┤         ├──────────────┤             │
│  │ payment_     │         │ download_    │             │
│  │   intents    │         │   records    │             │
│  │ payment_     │         │ generation_  │             │
│  │   methods    │         │   analytics  │             │
│  │ transactions │         └──────────────┘             │
│  └──────────────┘                                        │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Table Schemas

### 1. Users Table

**Table Name:** `users`

**Description:** Stores user account information.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    oauth_provider VARCHAR(50) CHECK (oauth_provider IN ('google')),
    oauth_provider_id VARCHAR(255),
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_oauth ON users(oauth_provider, oauth_provider_id);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Unique constraint for OAuth
CREATE UNIQUE INDEX idx_users_oauth_unique 
    ON users(oauth_provider, oauth_provider_id) 
    WHERE oauth_provider IS NOT NULL;

-- Comments
COMMENT ON TABLE users IS 'User accounts and authentication data';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password (null for OAuth users)';
COMMENT ON COLUMN users.role IS 'User role: user or admin';
```

---

### 2. Child Profiles Table

**Table Name:** `child_profiles`

**Description:** Child information for personalized books.

```sql
CREATE TABLE child_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 0 AND age <= 18),
    gender VARCHAR(20) NOT NULL CHECK (gender IN ('male', 'female', 'other')),
    birth_date DATE,
    photo_url VARCHAR(500),
    books_created_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_child_profiles_user_id ON child_profiles(user_id);
CREATE INDEX idx_child_profiles_active ON child_profiles(user_id, is_active);

-- Comments
COMMENT ON TABLE child_profiles IS 'Child profiles for personalized book generation';
COMMENT ON COLUMN child_profiles.books_created_count IS 'Denormalized count of books created';
```

---

### 3. Addresses Table

**Table Name:** `addresses`

**Description:** Shipping and billing addresses.

```sql
CREATE TABLE addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country CHAR(2) NOT NULL,  -- ISO 3166-1 alpha-2
    phone VARCHAR(20) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_addresses_user_id ON addresses(user_id);
CREATE INDEX idx_addresses_default ON addresses(user_id, is_default);

-- Ensure only one default address per user
CREATE UNIQUE INDEX idx_addresses_user_default 
    ON addresses(user_id) 
    WHERE is_default = TRUE AND is_active = TRUE;

-- Comments
COMMENT ON TABLE addresses IS 'User shipping and billing addresses';
COMMENT ON COLUMN addresses.country IS 'ISO 3166-1 alpha-2 country code (e.g., US, GB)';
```

---

### 4. Book Templates Table

**Table Name:** `book_templates`

**Description:** Pre-designed book templates (story books and coloring books).

```sql
CREATE TABLE book_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    long_description TEXT,
    
    -- Type and categorization
    template_type VARCHAR(20) NOT NULL CHECK (template_type IN ('story_book', 'coloring_book')),
    book_type VARCHAR(20) CHECK (book_type IN ('single', 'series')),  -- For story books
    series_id UUID REFERENCES book_templates(id),  -- Self-referencing for series
    book_number INTEGER,  -- Position in series
    
    -- Classification
    genre VARCHAR(50) NOT NULL,
    age_group VARCHAR(20) NOT NULL CHECK (age_group IN ('0-2', '3-5', '6-8', '9-12')),
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),  -- For coloring books
    
    -- Pricing
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    
    -- Media
    cover_image_url VARCHAR(500) NOT NULL,
    preview_images JSONB DEFAULT '[]',  -- Array of preview image URLs
    
    -- Content
    total_pages INTEGER NOT NULL CHECK (total_pages > 0),
    features JSONB DEFAULT '[]',  -- Array of feature strings
    learning_outcomes JSONB DEFAULT '[]',  -- Array of learning outcomes
    
    -- Customization options
    customization_options JSONB DEFAULT '{}',
    
    -- Metadata
    tags JSONB DEFAULT '[]',  -- Array of tags
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_published BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_templates_type ON book_templates(template_type);
CREATE INDEX idx_templates_genre ON book_templates(genre);
CREATE INDEX idx_templates_age_group ON book_templates(age_group);
CREATE INDEX idx_templates_active ON book_templates(is_active, is_published);
CREATE INDEX idx_templates_series ON book_templates(series_id, book_number);
CREATE INDEX idx_templates_price ON book_templates(price);

-- GIN index for JSONB columns (for searching tags)
CREATE INDEX idx_templates_tags ON book_templates USING GIN(tags);

-- Full-text search
CREATE INDEX idx_templates_search ON book_templates 
    USING GIN(to_tsvector('english', title || ' ' || description));

-- Comments
COMMENT ON TABLE book_templates IS 'Pre-designed book templates catalog';
COMMENT ON COLUMN book_templates.preview_images IS 'JSON array of preview image URLs';
COMMENT ON COLUMN book_templates.customization_options IS 'JSON object with customization settings';
```

---

### 5. Generation Requests Table

**Table Name:** `generation_requests`

**Description:** Track book generation processes.

```sql
CREATE TABLE generation_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id UUID NOT NULL REFERENCES book_templates(id),
    child_id UUID REFERENCES child_profiles(id) ON DELETE SET NULL,
    
    -- Child info (denormalized for record keeping)
    child_name VARCHAR(100) NOT NULL,
    child_age INTEGER NOT NULL,
    child_gender VARCHAR(20) NOT NULL,
    
    -- Photos
    photo_urls JSONB NOT NULL,  -- Array of S3 URLs
    
    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'queued' 
        CHECK (status IN ('queued', 'processing', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    current_step VARCHAR(100),
    
    -- Queue info
    queue_position INTEGER,
    
    -- Result
    book_id UUID REFERENCES generated_books(id),
    
    -- Error handling
    error_code VARCHAR(50),
    error_message TEXT,
    error_details JSONB,
    
    -- Timing
    estimated_completion_time INTEGER,  -- seconds
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    generation_duration INTEGER,  -- seconds
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_generation_user_id ON generation_requests(user_id);
CREATE INDEX idx_generation_template_id ON generation_requests(template_id);
CREATE INDEX idx_generation_status ON generation_requests(status);
CREATE INDEX idx_generation_created ON generation_requests(created_at DESC);
CREATE INDEX idx_generation_queue ON generation_requests(status, queue_position) 
    WHERE status = 'queued';

-- Comments
COMMENT ON TABLE generation_requests IS 'Book generation process tracking';
COMMENT ON COLUMN generation_requests.photo_urls IS 'JSON array of uploaded photo S3 URLs';
COMMENT ON COLUMN generation_requests.generation_duration IS 'Total time taken in seconds';
```

---

### 6. Generated Books Table

**Table Name:** `generated_books`

**Description:** Successfully generated personalized books.

```sql
CREATE TABLE generated_books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id UUID NOT NULL REFERENCES book_templates(id),
    generation_request_id UUID REFERENCES generation_requests(id),
    child_id UUID REFERENCES child_profiles(id) ON DELETE SET NULL,
    
    -- Child info (denormalized)
    child_name VARCHAR(100) NOT NULL,
    child_age INTEGER NOT NULL,
    child_gender VARCHAR(20) NOT NULL,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'preview' 
        CHECK (status IN ('preview', 'purchased')),
    is_purchased BOOLEAN DEFAULT FALSE,
    
    -- Media
    cover_image_url VARCHAR(500) NOT NULL,
    watermarked_pdf_url VARCHAR(500) NOT NULL,  -- Preview PDF with watermark
    full_pdf_url VARCHAR(500),  -- Only populated after purchase
    
    -- Content
    total_pages INTEGER NOT NULL,
    
    -- Purchase info
    purchased_at TIMESTAMP WITH TIME ZONE,
    order_id UUID,  -- Will be added as FK later
    
    -- Generation metrics
    generation_duration INTEGER,  -- seconds
    
    -- Access control
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_books_user_id ON generated_books(user_id);
CREATE INDEX idx_books_template_id ON generated_books(template_id);
CREATE INDEX idx_books_child_id ON generated_books(child_id);
CREATE INDEX idx_books_status ON generated_books(status);
CREATE INDEX idx_books_purchased ON generated_books(is_purchased);
CREATE INDEX idx_books_created ON generated_books(created_at DESC);

-- Comments
COMMENT ON TABLE generated_books IS 'Successfully generated personalized books';
COMMENT ON COLUMN generated_books.watermarked_pdf_url IS 'Preview PDF with watermark (first 2 pages)';
COMMENT ON COLUMN generated_books.full_pdf_url IS 'Full PDF without watermark (only after purchase)';
```

---

### 7. Book Pages Table

**Table Name:** `book_pages`

**Description:** Individual pages of generated books.

```sql
CREATE TABLE book_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES generated_books(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL CHECK (page_number > 0),
    
    -- Content
    text_content TEXT,
    image_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    
    -- Preview status
    is_preview BOOLEAN DEFAULT FALSE,  -- First 2 pages
    is_blurred BOOLEAN DEFAULT FALSE,  -- Locked preview pages
    has_watermark BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_pages_book_id ON book_pages(book_id);
CREATE INDEX idx_pages_page_number ON book_pages(book_id, page_number);
CREATE INDEX idx_pages_preview ON book_pages(book_id, is_preview);

-- Unique constraint
CREATE UNIQUE INDEX idx_pages_unique ON book_pages(book_id, page_number);

-- Comments
COMMENT ON TABLE book_pages IS 'Individual pages of generated books';
COMMENT ON COLUMN book_pages.is_preview IS 'TRUE for first 2 pages shown in preview';
```

---

### 8. Carts Table

**Table Name:** `carts`

**Description:** Shopping carts for users.

```sql
CREATE TABLE carts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Discount
    discount_code VARCHAR(50),
    discount_amount DECIMAL(10, 2) DEFAULT 0.00,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_carts_user_id ON carts(user_id);
CREATE INDEX idx_carts_active ON carts(is_active);

-- Comments
COMMENT ON TABLE carts IS 'User shopping carts';
COMMENT ON COLUMN carts.discount_code IS 'Applied discount/promo code';
```

---

### 9. Cart Items Table

**Table Name:** `cart_items`

**Description:** Items in shopping carts.

```sql
CREATE TABLE cart_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cart_id UUID NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    book_id UUID NOT NULL REFERENCES generated_books(id) ON DELETE CASCADE,
    
    -- Product details
    format VARCHAR(20) NOT NULL CHECK (format IN ('digital', 'softcover', 'hardcover')),
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    
    -- Pricing (snapshot at time of adding to cart)
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    total_price DECIMAL(10, 2) NOT NULL CHECK (total_price >= 0),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_cart_items_cart_id ON cart_items(cart_id);
CREATE INDEX idx_cart_items_book_id ON cart_items(book_id);

-- Unique constraint: one book per cart (can change format/quantity)
CREATE UNIQUE INDEX idx_cart_items_unique ON cart_items(cart_id, book_id);

-- Comments
COMMENT ON TABLE cart_items IS 'Items in user shopping carts';
COMMENT ON COLUMN cart_items.format IS 'Product format: digital, softcover, or hardcover';
```

---

### 10. Orders Table

**Table Name:** `orders`

**Description:** Customer orders.

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) UNIQUE NOT NULL,  -- SB-2026-000123
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    
    -- Status
    status VARCHAR(30) NOT NULL DEFAULT 'pending_payment'
        CHECK (status IN (
            'pending_payment', 'payment_confirmed', 'processing',
            'shipped', 'delivered', 'completed', 'cancelled', 'refunded'
        )),
    
    -- Pricing
    subtotal DECIMAL(10, 2) NOT NULL CHECK (subtotal >= 0),
    shipping DECIMAL(10, 2) DEFAULT 0.00 CHECK (shipping >= 0),
    tax DECIMAL(10, 2) DEFAULT 0.00 CHECK (tax >= 0),
    discount DECIMAL(10, 2) DEFAULT 0.00 CHECK (discount >= 0),
    total DECIMAL(10, 2) NOT NULL CHECK (total >= 0),
    
    -- Addresses (snapshot at time of order)
    shipping_address_id UUID REFERENCES addresses(id),
    shipping_address_snapshot JSONB,  -- Full address data
    billing_address_id UUID REFERENCES addresses(id),
    billing_address_snapshot JSONB,
    
    -- Shipping
    shipping_method VARCHAR(50),
    tracking_number VARCHAR(100),
    estimated_delivery DATE,
    
    -- Payment
    payment_intent_id VARCHAR(255),  -- Stripe Payment Intent ID
    payment_method VARCHAR(50),
    payment_status VARCHAR(30) DEFAULT 'pending'
        CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')),
    
    -- Cancellation/Refund
    cancellation_reason TEXT,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    refund_amount DECIMAL(10, 2),
    refunded_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);
CREATE INDEX idx_orders_payment_intent ON orders(payment_intent_id);

-- Comments
COMMENT ON TABLE orders IS 'Customer orders';
COMMENT ON COLUMN orders.order_number IS 'Human-readable order number (e.g., SB-2026-000123)';
COMMENT ON COLUMN orders.shipping_address_snapshot IS 'Address data snapshot at order time';
```

---

### 11. Order Items Table

**Table Name:** `order_items`

**Description:** Items in orders.

```sql
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    book_id UUID NOT NULL REFERENCES generated_books(id) ON DELETE RESTRICT,
    
    -- Product details (snapshot at order time)
    book_title VARCHAR(255) NOT NULL,
    child_name VARCHAR(100) NOT NULL,
    template_title VARCHAR(255) NOT NULL,
    cover_image_url VARCHAR(500),
    
    -- Pricing
    format VARCHAR(20) NOT NULL CHECK (format IN ('digital', 'softcover', 'hardcover')),
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    total_price DECIMAL(10, 2) NOT NULL CHECK (total_price >= 0),
    
    -- Digital delivery
    download_url VARCHAR(500),  -- Signed S3 URL for digital purchases
    download_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_book_id ON order_items(book_id);

-- Comments
COMMENT ON TABLE order_items IS 'Individual items in orders';
COMMENT ON COLUMN order_items.download_url IS 'Temporary signed URL for digital book download';
```

---

### 12. Payment Intents Table

**Table Name:** `payment_intents`

**Description:** Stripe payment intents.

```sql
CREATE TABLE payment_intents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_payment_intent_id VARCHAR(255) UNIQUE NOT NULL,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Amount
    amount INTEGER NOT NULL,  -- In cents
    currency CHAR(3) DEFAULT 'usd',
    
    -- Status
    status VARCHAR(30) NOT NULL
        CHECK (status IN (
            'requires_payment_method', 'requires_confirmation', 'requires_action',
            'processing', 'succeeded', 'canceled', 'requires_capture'
        )),
    
    -- Client secret for frontend
    client_secret VARCHAR(500),
    
    -- Payment method
    payment_method_id VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_payment_intents_stripe_id ON payment_intents(stripe_payment_intent_id);
CREATE INDEX idx_payment_intents_order_id ON payment_intents(order_id);
CREATE INDEX idx_payment_intents_user_id ON payment_intents(user_id);
CREATE INDEX idx_payment_intents_status ON payment_intents(status);

-- Comments
COMMENT ON TABLE payment_intents IS 'Stripe payment intents for orders';
COMMENT ON COLUMN payment_intents.amount IS 'Amount in cents (e.g., 2179 = $21.79)';
```

---

### 13. Payment Methods Table

**Table Name:** `payment_methods`

**Description:** Saved payment methods.

```sql
CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_payment_method_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Type
    type VARCHAR(30) NOT NULL CHECK (type IN ('card', 'apple_pay', 'google_pay')),
    
    -- Card details (for display only)
    card_brand VARCHAR(30),
    card_last4 CHAR(4),
    card_exp_month INTEGER CHECK (card_exp_month BETWEEN 1 AND 12),
    card_exp_year INTEGER,
    card_country CHAR(2),
    
    -- Settings
    is_default BOOLEAN DEFAULT FALSE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_payment_methods_user_id ON payment_methods(user_id);
CREATE INDEX idx_payment_methods_stripe_id ON payment_methods(stripe_payment_method_id);
CREATE INDEX idx_payment_methods_default ON payment_methods(user_id, is_default);

-- Ensure only one default payment method per user
CREATE UNIQUE INDEX idx_payment_methods_user_default 
    ON payment_methods(user_id) 
    WHERE is_default = TRUE AND is_active = TRUE;

-- Comments
COMMENT ON TABLE payment_methods IS 'User saved payment methods';
COMMENT ON COLUMN payment_methods.card_last4 IS 'Last 4 digits of card (for display)';
```

---

### 14. Transactions Table

**Table Name:** `transactions`

**Description:** Payment transaction log.

```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_intent_id UUID NOT NULL REFERENCES payment_intents(id) ON DELETE CASCADE,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Amount
    amount INTEGER NOT NULL,  -- In cents
    currency CHAR(3) DEFAULT 'usd',
    
    -- Status
    status VARCHAR(30) NOT NULL CHECK (status IN ('succeeded', 'failed', 'refunded')),
    
    -- Payment details
    payment_method_type VARCHAR(30),
    card_brand VARCHAR(30),
    card_last4 CHAR(4),
    
    -- Fees (in cents)
    stripe_fee INTEGER DEFAULT 0,
    application_fee INTEGER DEFAULT 0,
    net_amount INTEGER NOT NULL,
    
    -- Error (if failed)
    error_code VARCHAR(50),
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_transactions_payment_intent ON transactions(payment_intent_id);
CREATE INDEX idx_transactions_order_id ON transactions(order_id);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created ON transactions(created_at DESC);

-- Comments
COMMENT ON TABLE transactions IS 'Payment transaction log for accounting and analytics';
COMMENT ON COLUMN transactions.net_amount IS 'Amount after fees (in cents)';
```

---

### 15. Download Records Table

**Table Name:** `download_records`

**Description:** Track book downloads for analytics.

```sql
CREATE TABLE download_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES generated_books(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    
    -- Download details
    format VARCHAR(20) NOT NULL CHECK (format IN ('pdf', 'epub')),
    file_size BIGINT,  -- In bytes
    
    -- Source tracking
    source VARCHAR(50),  -- 'dashboard', 'email', 'api'
    device VARCHAR(50),  -- 'desktop', 'mobile', 'tablet'
    
    -- Network info
    ip_address INET,
    user_agent TEXT,
    
    -- Timestamp
    downloaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_downloads_book_id ON download_records(book_id);
CREATE INDEX idx_downloads_user_id ON download_records(user_id);
CREATE INDEX idx_downloads_order_id ON download_records(order_id);
CREATE INDEX idx_downloads_date ON download_records(downloaded_at DESC);

-- Comments
COMMENT ON TABLE download_records IS 'Book download analytics and tracking';
COMMENT ON COLUMN download_records.ip_address IS 'IP address of downloader (for security)';
```

---

### 16. Refresh Tokens Table

**Table Name:** `refresh_tokens`

**Description:** JWT refresh tokens for authentication.

```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,  -- Hashed refresh token
    
    -- Metadata
    device_info TEXT,
    ip_address INET,
    user_agent TEXT,
    
    -- Expiry
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Status
    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
CREATE INDEX idx_refresh_tokens_active ON refresh_tokens(user_id, is_revoked) 
    WHERE is_revoked = FALSE;

-- Auto-delete expired tokens (can be done via cron job)
-- DELETE FROM refresh_tokens WHERE expires_at < NOW() AND is_revoked = FALSE;

-- Comments
COMMENT ON TABLE refresh_tokens IS 'JWT refresh tokens for authentication';
COMMENT ON COLUMN refresh_tokens.token_hash IS 'SHA-256 hash of refresh token';
```

---

## Relationships & ERD

### Entity Relationship Diagram

```
┌──────────┐
│  users   │──┐
└──────────┘  │
              ├─ (1:N) ─┬─► child_profiles
              │         ├─► addresses
              │         ├─► carts
              │         ├─► orders
              │         ├─► generated_books
              │         ├─► generation_requests
              │         ├─► payment_methods
              │         └─► refresh_tokens
              │
┌────────────────┐
│ book_templates │──┐
└────────────────┘  │
                    ├─ (1:N) ─► generation_requests
                    └─ (1:N) ─► generated_books
                    
┌──────────────────┐
│ generated_books  │──┐
└──────────────────┘  │
                      ├─ (1:N) ─► book_pages
                      ├─ (1:N) ─► cart_items
                      ├─ (1:N) ─► order_items
                      └─ (1:N) ─► download_records
                      
┌────────┐
│ carts  │─ (1:N) ─► cart_items
└────────┘

┌────────┐
│ orders │──┐
└────────┘  │
            ├─ (1:N) ─► order_items
            ├─ (1:1) ─► payment_intents
            └─ (1:N) ─► transactions
            
┌─────────────────┐
│ payment_intents │─ (1:N) ─► transactions
└─────────────────┘
```

### Key Relationships

1. **User → Child Profiles** (1:N)
   - One user can have multiple child profiles
   - Cascade delete: Delete user removes children

2. **User → Generated Books** (1:N)
   - One user can have many generated books
   - Restrict delete: Cannot delete user with books

3. **Template → Generated Books** (1:N)
   - One template can be used for many books
   - Restrict delete: Cannot delete template in use

4. **Book → Pages** (1:N)
   - One book has many pages
   - Cascade delete: Delete book removes pages

5. **User → Orders** (1:N)
   - One user can have many orders
   - Restrict delete: Cannot delete user with orders

6. **Order → Order Items** (1:N)
   - One order contains many items
   - Cascade delete: Delete order removes items

7. **Order → Payment Intent** (1:1)
   - Each order has one payment intent
   - Cascade delete: Delete order removes payment intent

---

## Indexes

### Performance-Critical Indexes

```sql
-- User lookups
CREATE INDEX idx_users_email_lower ON users(LOWER(email));

-- Book template searches
CREATE INDEX idx_templates_full_search ON book_templates 
    USING GIN(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Recent generations
CREATE INDEX idx_generation_recent ON generation_requests(user_id, created_at DESC);

-- User's purchased books
CREATE INDEX idx_books_user_purchased ON generated_books(user_id, is_purchased, created_at DESC);

-- Active orders
CREATE INDEX idx_orders_active ON orders(user_id, status) 
    WHERE status NOT IN ('completed', 'cancelled');

-- Payment processing
CREATE INDEX idx_payment_intents_pending ON payment_intents(status) 
    WHERE status IN ('requires_payment_method', 'requires_confirmation', 'processing');
```

---

## Constraints

### Check Constraints

```sql
-- Price validations
ALTER TABLE book_templates 
    ADD CONSTRAINT chk_price_positive CHECK (price > 0);

ALTER TABLE order_items 
    ADD CONSTRAINT chk_unit_price_positive CHECK (unit_price >= 0);

-- Age validations
ALTER TABLE child_profiles 
    ADD CONSTRAINT chk_age_range CHECK (age >= 0 AND age <= 18);

-- Email format
ALTER TABLE users 
    ADD CONSTRAINT chk_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Order total consistency
ALTER TABLE orders 
    ADD CONSTRAINT chk_order_total CHECK (total = subtotal + shipping + tax - discount);
```

### Foreign Key Constraints with Actions

```sql
-- Prevent deletion of templates with generated books
ALTER TABLE generated_books 
    ADD CONSTRAINT fk_generated_books_template 
    FOREIGN KEY (template_id) REFERENCES book_templates(id) 
    ON DELETE RESTRICT;

-- Cascade delete child data when user is deleted
ALTER TABLE child_profiles 
    ADD CONSTRAINT fk_child_profiles_user 
    FOREIGN KEY (user_id) REFERENCES users(id) 
    ON DELETE CASCADE;

-- Prevent deletion of books with orders
ALTER TABLE order_items 
    ADD CONSTRAINT fk_order_items_book 
    FOREIGN KEY (book_id) REFERENCES generated_books(id) 
    ON DELETE RESTRICT;
```

---

## Views

### 1. User Stats View

```sql
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id AS user_id,
    u.email,
    u.first_name,
    u.last_name,
    COUNT(DISTINCT cp.id) AS child_count,
    COUNT(DISTINCT gb.id) AS book_count,
    COUNT(DISTINCT CASE WHEN gb.is_purchased THEN gb.id END) AS purchased_book_count,
    COUNT(DISTINCT o.id) AS order_count,
    COALESCE(SUM(o.total), 0) AS total_spent,
    MAX(o.created_at) AS last_order_date,
    u.created_at AS user_since
FROM users u
LEFT JOIN child_profiles cp ON u.id = cp.user_id AND cp.is_active = TRUE
LEFT JOIN generated_books gb ON u.id = gb.user_id AND gb.is_active = TRUE
LEFT JOIN orders o ON u.id = o.user_id AND o.status = 'completed'
GROUP BY u.id;

-- Comments
COMMENT ON VIEW user_stats IS 'Aggregated user statistics and activity';
```

### 2. Order Summary View

```sql
CREATE OR REPLACE VIEW order_summary AS
SELECT 
    o.id,
    o.order_number,
    o.user_id,
    u.email AS user_email,
    o.status,
    o.payment_status,
    o.total,
    COUNT(oi.id) AS item_count,
    o.created_at,
    o.updated_at
FROM orders o
JOIN users u ON o.user_id = u.id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, u.email
ORDER BY o.created_at DESC;

-- Comments
COMMENT ON VIEW order_summary IS 'Order summary with item counts';
```

---

## Migration Strategy

### Initial Setup

```bash
# Install Alembic
pip install alembic

# Initialize Alembic
alembic init alembic

# Edit alembic.ini with database URL
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost/storybloom

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

### Migration Files Structure

```
alembic/
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_add_phone_to_users.py
│   ├── 003_add_generation_indexes.py
│   └── ...
├── env.py
├── script.py.mako
└── README
```

### Example Migration

```python
"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-02-14 10:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        # ... other columns
    )
    
    # Create indexes
    op.create_index('idx_users_email', 'users', ['email'])
    
def downgrade():
    op.drop_table('users')
```

---

## Database Maintenance

### Regular Maintenance Tasks

```sql
-- Vacuum and analyze tables weekly
VACUUM ANALYZE users;
VACUUM ANALYZE generated_books;
VACUUM ANALYZE orders;

-- Reindex tables monthly
REINDEX TABLE book_templates;
REINDEX TABLE generated_books;

-- Clean up expired refresh tokens daily
DELETE FROM refresh_tokens 
WHERE expires_at < NOW() - INTERVAL '7 days';

-- Archive old generation requests (older than 90 days)
-- Move to archive table or delete
DELETE FROM generation_requests 
WHERE created_at < NOW() - INTERVAL '90 days' 
AND status IN ('completed', 'failed', 'cancelled');
```

### Backup Strategy

```bash
# Daily automated backups
pg_dump -Fc storybloom > backup_$(date +%Y%m%d).dump

# Point-in-time recovery setup
# Enable WAL archiving in postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /path/to/archive/%f'
```

---

## Performance Tuning

### PostgreSQL Configuration

```ini
# postgresql.conf recommendations

# Memory
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 64MB
maintenance_work_mem = 1GB

# Connections
max_connections = 200

# Query Planning
random_page_cost = 1.1  # For SSD
effective_io_concurrency = 200

# WAL
wal_buffers = 16MB
checkpoint_completion_target = 0.9
```

### Connection Pooling

```python
# Using SQLAlchemy with asyncpg
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/storybloom",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False
)
```

---

## Security Considerations

### Row-Level Security (RLS)

```sql
-- Enable RLS on sensitive tables
ALTER TABLE generated_books ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own books
CREATE POLICY user_books_policy ON generated_books
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::UUID);

-- Similar policies for other user-specific tables
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_orders_policy ON orders
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::UUID);
```

### Sensitive Data Encryption

```sql
-- Use pgcrypto for sensitive data
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Example: Encrypt payment method details
-- (In practice, Stripe handles this, but shown for reference)
```

### Audit Logging

```sql
-- Create audit log table
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    user_id UUID REFERENCES users(id),
    old_data JSONB,
    new_data JSONB,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create trigger function for audit logging
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_log (table_name, record_id, action, old_data)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', row_to_json(OLD));
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_log (table_name, record_id, action, old_data, new_data)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_log (table_name, record_id, action, new_data)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', row_to_json(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to important tables
CREATE TRIGGER orders_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON orders
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
```

---

## Data Retention Policy

### Retention Periods

| Data Type | Retention Period | Action |
|-----------|-----------------|---------|
| User accounts | Indefinite (until user deletes) | Soft delete + 30 day grace |
| Generated books | Indefinite (user's property) | Keep forever |
| Generation requests | 90 days | Archive or delete |
| Orders | 7 years | Required for accounting |
| Download records | 1 year | Archive old records |
| Audit logs | 2 years | Archive to cold storage |
| Refresh tokens | 7 days after expiry | Auto-delete |

---

## Monitoring Queries

### Slow Query Monitoring

```sql
-- Find slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;

-- Table size monitoring
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage monitoring
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

---

## Summary

This database schema provides:

✅ **Scalability**: UUID primary keys, proper indexing  
✅ **Data Integrity**: Foreign keys, check constraints  
✅ **Performance**: Strategic indexes, views  
✅ **Security**: RLS, audit logging  
✅ **Maintainability**: Clear structure, documentation  
✅ **Flexibility**: JSONB for dynamic data

**Total Tables**: 16 core tables + views  
**Total Indexes**: 60+ for optimal query performance  
**Normalization**: 3NF with strategic denormalization

---

**Next Steps**:
1. Review and adjust based on specific requirements
2. Set up Alembic migrations
3. Create SQLAlchemy models
4. Implement seed data
5. Set up database backups
6. Configure monitoring
