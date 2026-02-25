# 🚀 Story Bloom -- Frontend Application Prompt (For bolt.new)

Build a production-ready enterprise-grade Next.js (App Router) frontend
application named:

# 🌸 Story Bloom

This application is strictly a frontend client application.

------------------------------------------------------------------------

## ⚠️ Important Architecture Constraints

-   Backend will be implemented separately.
-   Authentication will be handled by backend.
-   Payments will be handled by backend.
-   Database will exist in backend.
-   This project must implement frontend pieces only.
-   All API calls must be abstracted and mockable.
-   Use JSON seed data for now.
-   Do NOT use Supabase.
-   Do NOT use Prisma.
-   Do NOT use Next.js API routes.
-   Do NOT use Server Actions.
-   Do NOT directly import JSON into UI components.

------------------------------------------------------------------------

# 🧱 Tech Stack Requirements

Must use:

-   Next.js (App Router)
-   TypeScript
-   Tailwind CSS
-   TanStack React Query
-   Axios (for API abstraction)
-   React Hook Form
-   Zod (for validation)
-   Framer Motion
-   A UI component library compatible with playful children theme (e.g.,
    shadcn/ui)

------------------------------------------------------------------------

# 🏗 Enterprise-Grade Architecture

Structure the app using a feature-based scalable architecture:

src/ app/ components/ ui/ layout/ shared/ features/ books/ components/
hooks/ services/ types/ preview/ checkout/ auth/ user/ lib/ api/
axios.ts endpoints.ts react-query/ queryClient.ts utils/ constants/
mock-api/ books.json coloring-books.json pricing.json user.json
providers/ types/

Architecture Principles:

-   Feature-based modular structure
-   UI components separated from business logic
-   API calls isolated in service layer
-   React Query used for all server state
-   Easy replacement of mock services with real REST APIs
-   Fully typed with TypeScript

------------------------------------------------------------------------

# 🔌 API Integration Pattern (Critical Requirement)

Even though backend exists separately, simulate API calls using mock
services.

1️⃣ Create Axios Base Instance\
lib/api/axios.ts

2️⃣ Define Endpoints\
lib/api/endpoints.ts

Example endpoints:

GET /books\
GET /books/:id\
POST /books/generate\
GET /books/:id/preview\
POST /checkout\
GET /user/orders

3️⃣ Mock Service Layer

Inside:\
features/books/services/books.service.ts

Each function must:

-   Return Promise
-   Simulate 500ms delay
-   Read from JSON
-   Return properly typed data

All data must flow through:

Component → React Query → Service → Mock Data

Later replace with:

return axios.get('/books')

------------------------------------------------------------------------

# 🎨 UI & THEME DESIGN

The theme must be extremely attractive to children.

Color Palette (Pastel):

-   Sky Blue
-   Baby Pink
-   Lavender
-   Peach
-   Soft Yellow

Style Guidelines:

-   Large rounded corners
-   Soft drop shadows
-   Floating cloud background animations
-   Sparkle accents
-   Smooth page transitions
-   Cartoon-friendly heading fonts
-   Gradient backgrounds
-   Animated micro-interactions

------------------------------------------------------------------------

# 🌐 Core Pages

Implement these routes:

/\
/story-books\
/coloring-books\
/create/\[bookId\]\
/preview/\[bookId\]\
/checkout/\[bookId\]\
/dashboard\
/pricing\
/about\
/login

------------------------------------------------------------------------

# 📚 Story Books Page

Must include:

-   Search bar
-   Filter sidebar (Age group, Genre, Type, Price range)
-   Sort dropdown
-   Responsive card grid

Each book card includes:

-   Cover image
-   Title
-   Description
-   Age group
-   Genre
-   Type
-   Price
-   Preview button
-   Create button

------------------------------------------------------------------------

# 🎨 Coloring Books Page

Same layout as story books but without series filter.

------------------------------------------------------------------------

# 📖 Seed Story Templates (10)

1.  My First Adventure\
2.  The Magical Forest Quest\
3.  Super Kid Saves the Day (Series)\
4.  Princess of the Rainbow Kingdom (Series)\
5.  Dino Explorer\
6.  Space Mission Star Kid (Series)\
7.  Underwater Treasure Hunt\
8.  Jungle Detective (Series)\
9.  Time Travel Twins (Series)\
10. Young Inventor's Big Idea

Each object structure:

{ "id": "","title": "","type": "single" \| "series", "genre":
"","ageGroup": "","price": 0, "description": "","coverImage":
"","totalPages": 0 }

------------------------------------------------------------------------

# 🎨 Seed Coloring Templates (10)

Each object structure:

{ "id": "","title": "","genre": "","ageGroup": "","price": 0,
"description": "","coverImage": "","totalPages": 0 }

------------------------------------------------------------------------

# 👶 Create Book Flow

Route: /create/\[bookId\]

Form fields:

-   Child Name
-   Age
-   Gender
-   Parent Email
-   Upload 1--3 photos

Use React Hook Form + Zod.

On submit:

-   Call mock generateBook API
-   Show animated loader: "Your book is blooming..."
-   Redirect to preview

------------------------------------------------------------------------

# 👀 Preview Page

Route: /preview/\[bookId\]

-   Show only 2 preview pages
-   Watermark overlay
-   Blurred locked thumbnails
-   CTA button: Unlock Full Book

------------------------------------------------------------------------

# 💳 Checkout Page (Frontend Only)

Route: /checkout/\[bookId\]

-   Digital copy
-   Softcover
-   Hardcover

On click:

-   Trigger mock API
-   Show success animation
-   Redirect to dashboard

------------------------------------------------------------------------

# 👤 Dashboard Page

Route: /dashboard

-   Purchased books
-   Download button
-   Reorder print
-   Order status

------------------------------------------------------------------------

# 🔐 Authentication UI (Frontend Only)

-   Login page
-   Google button
-   Instagram button

No real OAuth logic. Use mock auth context.

------------------------------------------------------------------------

# 🔍 Search & Filtering Logic

-   Use React Query data
-   Apply filtering in custom hooks
-   Memoization
-   Dynamic updates without reload

------------------------------------------------------------------------

# 🌈 UX Enhancements

-   Floating clouds background
-   Sparkle cursor effects
-   Confetti on checkout success
-   Skeleton loaders
-   Smooth transitions
-   Empty & error states

------------------------------------------------------------------------

# 🧠 State Management

-   React Query → server state
-   Context → auth state
-   Local state → UI state

------------------------------------------------------------------------

# 🛠 Code Quality Requirements

-   Fully typed with TypeScript
-   Reusable components
-   Clean service abstraction
-   No business logic inside UI components
-   Loading + error handling everywhere
-   Easily replaceable API layer

------------------------------------------------------------------------

# 🔴 Critical Reminder

Authentication and Payment will come from backend.

This frontend must:

-   Only implement UI pieces
-   Only simulate API calls
-   Be easily pluggable into real backend later
-   Maintain enterprise-grade structure
