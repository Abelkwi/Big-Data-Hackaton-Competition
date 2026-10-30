# SMARTSAVE Rwanda — Backend Blueprint v1.0

> **Document Purpose:** Master technical design aligning frontend (ClaudeWEB2) with backend (smartsave-backend).  
> **Status:** Planning  
> **Frontend Completion:** ~85–90%  
> **Backend Completion:** ~25–35%

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [User Roles & Permissions](#2-user-roles--permissions)
3. [Django Apps Map](#3-django-apps-map)
4. [Database Model Catalog](#4-database-model-catalog)
5. [Frontend Page → Backend Mapping](#5-frontend-page--backend-mapping)
6. [API Endpoints (REST)](#6-api-endpoints-rest)
7. [Development Phases](#7-development-phases)
8. [Data Relationships Diagram](#8-data-relationships)
9. [Security & Configuration](#9-security--configuration)

---

## 1. System Architecture

```
┌─────────────────────────────────────┐
│         ClaudeWEB2 Frontend         │
│  (Static HTML/CSS/JS → API Client) │
└──────────────┬──────────────────────┘
               │ HTTP/HTTPS
               │ REST API (JSON)
               ▼
┌─────────────────────────────────────┐
│      Django REST Framework API      │
│         smartsave-backend           │
│                                     │
│  ┌───────┐ ┌──────┐ ┌──────────┐  │
│  │ Auth  │ │ API  │ │  Views   │  │
│  │ Tokens│ │Views │ │ (Admin)  │  │
│  └───┬───┘ └──┬───┘ └────┬─────┘  │
│      │        │          │        │
│      ▼        ▼          ▼        │
│  ┌──────────────────────────────┐  │
│  │      Django ORM / Models      │  │
│  └──────────────┬───────────────┘  │
│                 │                 │
└─────────────────┼─────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │   MySQL 8.x    │
         │  smartsave_db  │
         └────────────────┘
```

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API Framework | Django REST Framework (DRF) | Industry standard, permission classes, serializers, browsable API |
| Auth Method | JWT (SimpleJWT) + Session | SPA uses JWT, admin uses sessions |
| File Storage | Local `media/` (dev) → S3/Cloudinary (prod) | Simplicity now, scalable later |
| Database | MySQL 8.x | Already configured |
| Frontend Integration | Static files served by Django OR via separate deployment | Flexible for staging |

---

## 2. User Roles & Permissions

### Role Hierarchy

```
                            ┌──────────────┐
                            │  Admin       │
                            │ (superuser)  │
                            └──────┬───────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                        ▼                        ▼
   ┌───────────┐           ┌───────────┐           ┌───────────┐
   │  Farmer   │           │   Buyer   │           │    NGO    │
   └─────┬─────┘           └─────┬─────┘           └─────┬─────┘
         │                       │                       │
    (Can sell,             (Can buy,               (Can view,
     manage shop)          track orders)            donate, recover)
```

### Permission Matrix

| Feature | Anonymous | Farmer | Buyer | NGO | Admin |
|---------|-----------|--------|-------|-----|-------|
| Browse marketplace | ✓ | ✓ | ✓ | ✓ | ✓ |
| View product detail | ✓ | ✓ | ✓ | ✓ | ✓ |
| Register | ✓ | - | - | - | - |
| Create listing | ✗ | ✓ | ✗ | ✗ | ✓ |
| Place order | ✗ | ✗ | ✓ | ✗ | ✓ |
| Send message | ✗ | ✓ | ✓ | ✓ | ✓ |
| View dashboard | ✗ | ✓ | ✓ | ✓ | ✓ |
| Create blog post | ✗ | ✗ | ✗ | ✗ | ✓ |
| Manage all users | ✗ | ✗ | ✗ | ✗ | ✓ |
| Access reports | ✗ | ✗ | ✗ | ✓ | ✓ |
| Food recovery | ✗ | ✓ | ✗ | ✓ | ✓ |
| Innovation hub | ✗ | ✓ | ✓ | ✓ | ✓ |

---

## 3. Django Apps Map

### Current Apps (3)

| App | Purpose | Status |
|-----|---------|--------|
| `core` | Project settings, URLs, WSGI | ✅ Done |
| `accounts` | Users, profiles, auth | ⚡ Partial |
| `marketplace` | Products, orders, messages | ⚡ Partial |

### Target Apps (12)

```
smartsave-backend/
│
├── core/              # Project settings (DONE)
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py / asgi.py
│   └── views.py       # serve_static_page helper
│
├── accounts/          # Users, roles, profiles (PARTIAL)
│   ├── models.py      # Profile, FarmerFollow
│   ├── views.py       # register, login, logout, farmer_store
│   ├── serializers.py # (NEW) DRF serializers
│   ├── urls.py        #
│   └── admin.py       #
│
├── marketplace/       # Products, categories (PARTIAL)
│   ├── models.py      # Product, ProductImage, Category
│   ├── views.py       # CRUD, search, filter
│   ├── serializers.py # (NEW)
│   ├── urls.py
│   └── admin.py
│
├── orders/            # NEW APP
│   ├── models.py      # Order, OrderItem, Cart, CartItem
│   ├── views.py       # checkout, order lifecycle
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
│
├── messaging/         # NEW APP
│   ├── models.py      # Conversation, Message
│   ├── views.py       # inbox, send, conversation list
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
│
├── notifications/     # NEW APP
│   ├── models.py      # Notification
│   ├── views.py       # list, mark_read
│   ├── serializers.py
│   └── urls.py
│
├── blog/              # NEW APP
│   ├── models.py      # Post, Category, Comment
│   ├── views.py       # CRUD, listing
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
│
├── contact/           # NEW APP
│   ├── models.py      # ContactMessage
│   ├── views.py       # submit, list (admin)
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
│
├── innovation/        # NEW APP
│   ├── models.py      # Innovation, Idea, Vote
│   ├── views.py       # submit, browse, vote
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
│
├── recovery/          # NEW APP (Food Recovery / Donation)
│   ├── models.py      # RecoveryListing, Donation, Claim
│   ├── views.py       # list, claim, donate
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
│
├── dashboard/         # NEW APP (Analytics / aggregations)
│   ├── views.py       # aggregated stats per role
│   ├── serializers.py
│   └── urls.py
│
└── payments/          # NEW APP (optional, future)
    ├── models.py      # Payment, Transaction
    ├── views.py
    ├── serializers.py
    ├── urls.py
    └── admin.py
```

---

## 4. Database Model Catalog

### 4.1 `accounts` — Existing + Enhancements

#### Profile (EXISTING — needs enhancement)
| Field | Type | Notes |
|-------|------|-------|
| user | OneToOneField(User) | Core identity |
| role | CharField | farmer / buyer / ngo |
| phone | CharField(20) | |
| gender | CharField(10) | |
| date_of_birth | DateField | nullable |
| profile_photo | ImageField | upload_to="profiles/" |
| bio | TextField | |
| country | CharField(100) | default="Rwanda" |
| province | CharField(100) | Administrative level |
| district | CharField(100) | |
| sector | CharField(100) | |
| cell | CharField(100) | |
| village | CharField(100) | |
| latitude | DecimalField(9,6) | GPS |
| longitude | DecimalField(9,6) | GPS |
| organization | CharField(150) | For NGO/Cooperative |
| is_verified | BooleanField | |
| store_name | CharField(150) | Farmer's shop name |
| store_slug | SlugField | Unique |
| store_banner | ImageField | |
| store_description | TextField | |
| website | URLField | |
| facebook | URLField | Social links |
| instagram | URLField | |
| twitter | URLField | |
| created_at | DateTimeField | |
| updated_at | DateTimeField | |

#### FarmerFollow (EXISTING)
| Field | Type | Notes |
|-------|------|-------|
| follower | ForeignKey(User) | Who follows |
| farmer | ForeignKey(User) | Being followed |
| created_at | DateTimeField | |

#### ADD: NGO (NEW MODEL)
| Field | Type | Notes |
|-------|------|-------|
| profile | OneToOneField(Profile) | Links to profile |
| registration_number | CharField(50) | Official NGO reg |
| mission_statement | TextField | |
| focus_areas | CharField(200) | Comma-separated |
| operational_districts | JSONField | Array of districts |
| website | URLField | |
| is_approved | BooleanField | Admin verification |

#### ADD: Cooperative (NEW MODEL)
| Field | Type | Notes |
|-------|------|-------|
| name | CharField(200) | |
| slug | SlugField | Unique |
| logo | ImageField | |
| banner | ImageField | |
| description | TextField | |
| district | CharField(100) | |
| sector | CharField(100) | |
| member_count | PositiveIntegerField | |
| formed_date | DateField | |
| registration_number | CharField(50) | |
| is_verified | BooleanField | |
| admin | ForeignKey(User) | Cooperative admin |
| members | ManyToManyField(User) | Farmer members |
| created_at | DateTimeField | |

### 4.2 `marketplace` — Existing + Enhancements

#### ADD: Category (NEW MODEL)
| Field | Type | Notes |
|-------|------|-------|
| name | CharField(100) | e.g. Vegetables |
| slug | SlugField | Unique |
| description | TextField | |
| icon | CharField(50) | Icon identifier |
| display_order | PositiveIntegerField | |
| is_active | BooleanField | |

#### Product (EXISTING — add FK to Category)
| Field | Type | Notes |
|-------|------|-------|
| farmer | ForeignKey(User) | Product owner |
| category | ForeignKey(Category) | **CHANGE from CharField** |
| name | CharField(150) | |
| slug | SlugField | Unique |
| variety | CharField(100) | |
| description | TextField | |
| main_image | ImageField | |
| quantity | DecimalField(10,2) | |
| unit | CharField(20) | kg, bunch, piece |
| minimum_order | DecimalField(10,2) | |
| price_per_unit | DecimalField(12,2) | |
| province | CharField(100) | Origin location |
| district | CharField(100) | |
| sector | CharField(100) | |
| harvest_date | DateField | |
| expiry_date | DateField | |
| organic | BooleanField | |
| verification_status | CharField | pending/verified/rejected |
| availability_status | CharField | available/out_of_stock/reserved/sold |
| is_active | BooleanField | |
| is_featured | BooleanField | |
| views | PositiveIntegerField | |
| created_at | DateTimeField | |
| updated_at | DateTimeField | |

#### ProductImage (EXISTING)
| Field | Type |
|-------|------|
| product | ForeignKey(Product) |
| image | ImageField |
| caption | CharField(150) |
| display_order | PositiveIntegerField |
| uploaded_at | DateTimeField |

#### Review (EXISTING)
| Field | Type |
|-------|------|
| product | ForeignKey(Product) |
| buyer | ForeignKey(User) |
| rating | PositiveSmallIntegerField |
| comment | TextField |
| is_approved | BooleanField |
| created_at | DateTimeField |
| *Constraint:* unique_together(product, buyer) |

#### Wishlist (EXISTING)
| Field | Type |
|-------|------|
| user | ForeignKey(User) |
| product | ForeignKey(Product) |
| created_at | DateTimeField |
| *Constraint:* unique_together(user, product) |

### 4.3 `orders` — NEW APP

#### Cart (NEW)
| Field | Type | Notes |
|-------|------|-------|
| user | ForeignKey(User) | One cart per user |
| created_at | DateTimeField | |
| updated_at | DateTimeField | |

#### CartItem (NEW)
| Field | Type | Notes |
|-------|------|-------|
| cart | ForeignKey(Cart) | |
| product | ForeignKey(Product) | |
| quantity | DecimalField(10,2) | |
| unit_price | DecimalField(12,2) | Snapshot at add time |
| created_at | DateTimeField | |

#### Order (MOVE from marketplace to orders)
| Field | Type | Notes |
|-------|------|-------|
| order_number | CharField(20) | **ADD**: auto-generated unique |
| buyer | ForeignKey(User) | |
| farmer | ForeignKey(User) | **ADD**: direct farmer link |
| status | CharField | pending/accepted/rejected/processing/shipped/delivered/cancelled |
| payment_status | CharField | pending/paid/failed/refunded |
| delivery_address | TextField | |
| delivery_phone | CharField(20) | |
| buyer_note | TextField | |
| farmer_note | TextField | |
| subtotal | DecimalField(14,2) | **ADD** |
| delivery_fee | DecimalField(10,2) | **ADD**, default 0 |
| total | DecimalField(14,2) | **ADD** |
| ordered_at | DateTimeField | |
| updated_at | DateTimeField | |

#### OrderItem (NEW — replaces single product FK)
| Field | Type | Notes |
|-------|------|-------|
| order | ForeignKey(Order) | |
| product | ForeignKey(Product) | |
| quantity | DecimalField(10,2) | |
| unit_price | DecimalField(12,2) | |
| total_price | DecimalField(14,2) | |

#### ADD: OrderStatusLog (NEW)
| Field | Type | Notes |
|-------|------|-------|
| order | ForeignKey(Order) | |
| from_status | CharField | Previous status |
| to_status | CharField | New status |
| changed_by | ForeignKey(User) | Who made the change |
| note | TextField | |
| created_at | DateTimeField | |

### 4.4 `messaging` — NEW APP

#### Conversation (NEW)
| Field | Type | Notes |
|-------|------|-------|
| participants | ManyToManyField(User) | Usually 2 users |
| subject | CharField(200) | |
| product | ForeignKey(Product, null) | Optional context |
| created_at | DateTimeField | |
| updated_at | DateTimeField | |

#### Message (MOVE from marketplace)
| Field | Type | Notes |
|-------|------|-------|
| conversation | ForeignKey(Conversation) | |
| sender | ForeignKey(User) | |
| body | TextField | |
| is_read | BooleanField | |
| sender_deleted | BooleanField | |
| created_at | DateTimeField | |

### 4.5 `notifications` — NEW APP

#### Notification (NEW)
| Field | Type | Notes |
|-------|------|-------|
| recipient | ForeignKey(User) | |
| notification_type | CharField(30) | order_update/message/blog/recovery |
| title | CharField(200) | |
| body | TextField | |
| link | CharField(500) | URL to redirect |
| is_read | BooleanField | |
| created_at | DateTimeField | |

### 4.6 `blog` — NEW APP

#### BlogCategory (NEW)
| Field | Type |
|-------|------|
| name | CharField(100) |
| slug | SlugField |
| description | TextField |

#### BlogPost (NEW)
| Field | Type | Notes |
|-------|------|-------|
| author | ForeignKey(User) | Admin/staff |
| category | ForeignKey(BlogCategory) | |
| title | CharField(200) | |
| slug | SlugField | Unique |
| excerpt | TextField | |
| content | TextField | Rich text |
| featured_image | ImageField | |
| tags | CharField(200) | Comma-separated |
| is_published | BooleanField | |
| published_at | DateTimeField | |
| created_at | DateTimeField | |
| updated_at | DateTimeField | |

#### BlogComment (NEW)
| Field | Type |
|-------|------|
| post | ForeignKey(BlogPost) |
| author | ForeignKey(User) |
| body | TextField |
| is_approved | BooleanField |
| created_at | DateTimeField |

### 4.7 `contact` — NEW APP

#### ContactMessage (NEW)
| Field | Type | Notes |
|-------|------|-------|
| name | CharField(100) | |
| email | EmailField | |
| subject | CharField(200) | |
| message | TextField | |
| is_read | BooleanField | |
| replied | BooleanField | |
| created_at | DateTimeField | |

### 4.8 `innovation` — NEW APP

#### InnovationIdea (NEW)
| Field | Type | Notes |
|-------|------|-------|
| submitted_by | ForeignKey(User) | |
| title | CharField(200) | |
| slug | SlugField | |
| description | TextField | |
| problem_solved | TextField | |
| expected_impact | TextField | |
| category | CharField(50) | technology/technique/sustainability |
| status | CharField | draft/submitted/under_review/approved/rejected/implemented |
| attachments | FileField | |
| is_featured | BooleanField | |
| votes_count | PositiveIntegerField | Denormalized |
| created_at | DateTimeField | |
| updated_at | DateTimeField | |

#### InnovationVote (NEW)
| Field | Type |
|-------|------|
| idea | ForeignKey(InnovationIdea) |
| voter | ForeignKey(User) |
| created_at | DateTimeField |
| *Constraint:* unique_together(idea, voter) |

#### InnovationComment (NEW)
| Field | Type |
|-------|------|
| idea | ForeignKey(InnovationIdea) |
| author | ForeignKey(User) |
| body | TextField |
| created_at | DateTimeField |

### 4.9 `recovery` — NEW APP

#### RecoveryListing (NEW)
| Field | Type | Notes |
|-------|------|-------|
| donor | ForeignKey(User) | Farmer who donates |
| product | ForeignKey(Product, null) | |
| title | CharField(200) | |
| description | TextField | |
| quantity | DecimalField(10,2) | |
| unit | CharField(20) | |
| expiry_date | DateField | |
| pickup_location | TextField | |
| pickup_instructions | TextField | |
| status | CharField | available/claimed/completed/expired |
| created_at | DateTimeField | |
| updated_at | DateTimeField | |

#### DonationClaim (NEW)
| Field | Type | Notes |
|-------|------|-------|
| listing | ForeignKey(RecoveryListing) | |
| claimant | ForeignKey(User) | NGO or individual |
| quantity | DecimalField(10,2) | |
| notes | TextField | |
| status | CharField | pending/approved/collected/completed/cancelled |
| created_at | DateTimeField | |
| updated_at | DateTimeField | |

#### Donation (NEW — monetary)
| Field | Type | Notes |
|-------|------|-------|
| donor | ForeignKey(User) | |
| amount | DecimalField(12,2) | |
| ngo | ForeignKey(User, null) | Target NGO |
| message | TextField | |
| is_anonymous | BooleanField | |
| status | CharField | pending/completed/failed |
| created_at | DateTimeField | |

### 4.10 `payments` — FUTURE APP

#### Payment (NEW)
| Field | Type | Notes |
|-------|------|-------|
| order | ForeignKey(Order, null) | |
| user | ForeignKey(User) | |
| amount | DecimalField(14,2) | |
| method | CharField(30) | MTN Mobile Money / Airtel Money / Card |
| reference | CharField(100) | Transaction reference |
| status | CharField(30) | pending/success/failed |
| created_at | DateTimeField | |

---

## 5. Frontend Page → Backend Mapping

| # | Frontend Page | Backend View | App | Model(s) Used | API Endpoint(s) Needed |
|---|--------------|-------------|-----|--------------|----------------------|
| 1 | `index.html` | HomePageView | core | — | GET /api/home/stats/ |
| 2 | `about.html` | Static | core | — | — |
| 3 | `login.html` | LoginView | accounts | User | POST /api/auth/login/ |
| 4 | `register.html` | RegisterView | accounts | User, Profile | POST /api/auth/register/ |
| 5 | `register-farmer.html` | RegisterFarmerView | accounts | User, Profile | POST /api/auth/register/farmer/ |
| 6 | `register-buyer.html` | RegisterBuyerView | accounts | User, Profile | POST /api/auth/register/buyer/ |
| 7 | `register-ngo.html` | RegisterNGOView | accounts | User, Profile | POST /api/auth/register/ngo/ |
| 8 | `marketplace.html` | MarketplaceList | marketplace | Product, Category, Profile | GET /api/marketplace/ |
| 9 | `marketplace-product.html` | ProductDetail | marketplace | Product, Review, Wishlist | GET /api/marketplace/{slug}/ |
| 10 | `farmers.html` | FarmerList | accounts | Profile, User | GET /api/accounts/farmers/ |
| 11 | `farmer-profile.html` | FarmerStoreView | accounts | Profile, Product, Review | GET /api/accounts/store/{slug}/ |
| 12 | `cooperative-profile.html` | CooperativeDetail | accounts | Cooperative, User | GET /api/accounts/cooperatives/{slug}/ |
| 13 | `buyer-dashboard.html` | BuyerDashboard | dashboard | Order, Wishlist, Message | GET /api/dashboard/buyer/ |
| 14 | `blog.html` | BlogList | blog | BlogPost, BlogCategory | GET /api/blog/ |
| 15 | `blog-post.html` | BlogDetail | blog | BlogPost, BlogComment | GET /api/blog/{slug}/ |
| 16 | `contact.html` | ContactView | contact | ContactMessage | POST /api/contact/ |
| 17 | `innovation.html` | InnovationList | innovation | InnovationIdea | GET /api/innovation/ |
| 18 | `recovery.html` | RecoveryList | recovery | RecoveryListing, Donation | GET /api/recovery/ |
| 19 | `404.html` | — | core | — | — |

---

## 6. API Endpoints (REST)

### 6.1 Authentication (`/api/auth/`)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/auth/register/` | Register (any role) | ✗ |
| POST | `/api/auth/register/farmer/` | Farmer-specific registration | ✗ |
| POST | `/api/auth/register/buyer/` | Buyer-specific registration | ✗ |
| POST | `/api/auth/register/ngo/` | NGO-specific registration | ✗ |
| POST | `/api/auth/login/` | Login, returns JWT | ✗ |
| POST | `/api/auth/token/refresh/` | Refresh JWT | ✗ |
| POST | `/api/auth/logout/` | Invalidate token | ✓ |
| POST | `/api/auth/password/reset/` | Request reset email | ✗ |
| POST | `/api/auth/password/reset/confirm/` | Confirm reset | ✗ |
| GET | `/api/auth/profile/` | Get current user profile | ✓ |
| PUT | `/api/auth/profile/` | Update profile | ✓ |
| PUT | `/api/auth/profile/change-password/` | Change password | ✓ |

### 6.2 Marketplace (`/api/marketplace/`)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/marketplace/` | List products (filter, search, sort, paginate) | ✗ |
| GET | `/api/marketplace/featured/` | Featured products | ✗ |
| GET | `/api/marketplace/categories/` | All categories | ✗ |
| GET | `/api/marketplace/{slug}/` | Product detail | ✗ |
| POST | `/api/marketplace/` | Create product (farmer only) | ✓ |
| PUT | `/api/marketplace/{slug}/` | Update product (owner only) | ✓ |
| DELETE | `/api/marketplace/{slug}/` | Delete product (owner only) | ✓ |
| POST | `/api/marketplace/{slug}/review/` | Add/update review | ✓ |
| POST | `/api/marketplace/{slug}/wishlist/` | Toggle wishlist | ✓ |
| GET | `/api/marketplace/wishlist/` | User's wishlist | ✓ |

### 6.3 Orders (`/api/orders/`)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/orders/cart/` | Get current cart | ✓ |
| POST | `/api/orders/cart/add/` | Add item to cart | ✓ |
| PUT | `/api/orders/cart/item/{id}/` | Update cart item | ✓ |
| DELETE | `/api/orders/cart/item/{id}/` | Remove from cart | ✓ |
| POST | `/api/orders/checkout/` | Convert cart to order | ✓ |
| GET | `/api/orders/` | List user's orders | ✓ |
| GET | `/api/orders/{id}/` | Order detail | ✓ |
| PUT | `/api/orders/{id}/cancel/` | Cancel order (buyer) | ✓ |
| PUT | `/api/orders/{id}/status/` | Update status (farmer/admin) | ✓ |
| GET | `/api/orders/farmer/` | Orders for farmer's products | ✓ |

### 6.4 Messaging (`/api/messaging/`)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/messaging/conversations/` | List conversations | ✓ |
| POST | `/api/messaging/conversations/` | Start new conversation | ✓ |
| GET | `/api/messaging/conversations/{id}/` | Get messages in conversation | ✓ |
| POST | `/api/messaging/conversations/{id}/send/` | Send message | ✓ |
| PUT | `/api/messaging/messages/{id}/read/` | Mark as read | ✓ |

### 6.5 Notifications (`/api/notifications/`)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/notifications/` | List user's notifications | ✓ |
| PUT | `/api/notifications/{id}/read/` | Mark as read | ✓ |
| PUT | `/api/notifications/read-all/` | Mark all as read | ✓ |
| GET | `/api/notifications/unread-count/` | Unread count badge | ✓ |

### 6.6 Blog (`/api/blog/`)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/blog/` | List published posts | ✗ |
| GET | `/api/blog/categories/` | Blog categories | ✗ |
| GET | `/api/blog/{slug}/` | Post detail | ✗ |
| POST | `/api/blog/{slug}/comment/` | Add comment | ✓ |
| POST | `/api/blog/` | Create post (admin) | ✓(admin) |
| PUT | `/api/blog/{slug}/` | Update post (admin) | ✓(admin) |
| DELETE | `/api/blog/{slug}/` | Delete post (admin) | ✓(admin) |

### 6.7 Contact (`/api/contact/`)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/contact/` | Submit contact form | ✗ |
| GET | `/api/contact/` | List messages (admin) | ✓(admin) |
| PUT | `/api/contact/{id}/read/` | Mark as read (admin) | ✓(admin) |

### 6.8 Innovation (`/api/innovation/`)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/innovation/` | List ideas | ✗ |
| POST | `/api/innovation/` | Submit idea | ✓ |
| GET | `/api/innovation/{slug}/` | Idea detail | ✗ |
| POST | `/api/innovation/{slug}/vote/` | Toggle vote | ✓ |
| POST | `/api/innovation/{slug}/comment/` | Add comment | ✓ |
| GET | `/api/innovation/featured/` | Featured ideas | ✗ |

### 6.9 Recovery (`/api/recovery/`)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/recovery/` | List recovery listings | ✗ |
| POST | `/api/recovery/` | Create listing (farmer) | ✓ |
| GET | `/api/recovery/{id}/` | Listing detail | ✗ |
| POST | `/api/recovery/{id}/claim/` | Claim listing (NGO) | ✓ |
| GET | `/api/recovery/donations/` | List monetary donations | ✗ |
| POST | `/api/recovery/donations/` | Make donation | ✓ |

### 6.10 Dashboard (`/api/dashboard/`)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/dashboard/farmer/` | Farmer dashboard stats | ✓(farmer) |
| GET | `/api/dashboard/buyer/` | Buyer dashboard stats | ✓(buyer) |
| GET | `/api/dashboard/ngo/` | NGO dashboard stats | ✓(ngo) |
| GET | `/api/dashboard/admin/` | Admin dashboard stats | ✓(admin) |

### 6.11 Accounts (`/api/accounts/`)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/accounts/farmers/` | List farmers | ✗ |
| GET | `/api/accounts/farmers/{slug}/` | Farmer store detail | ✗ |
| GET | `/api/accounts/cooperatives/` | List cooperatives | ✗ |
| GET | `/api/accounts/cooperatives/{slug}/` | Cooperative detail | ✗ |
| POST | `/api/accounts/farmers/{slug}/follow/` | Toggle follow | ✓ |

### 6.12 Home (`/api/home/`)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/home/stats/` | Platform stats (counters) | ✗ |
| GET | `/api/home/featured-products/` | Featured for homepage | ✗ |
| GET | `/api/home/testimonials/` | Testimonials | ✗ |

---

## 7. Development Phases

### Phase 1: Foundation Stabilization (Week 1)
**Goal:** Clean up existing code, add env vars, improve security

- [ ] Add `python-decouple` for `.env` file management
- [ ] Extract SECRET_KEY, DB credentials, DEBUG to `.env`
- [ ] Add `django-cors-headers` for CORS support
- [ ] Add `djangorestframework` + `djangorestframework-simplejwt`
- [ ] Review and fix `accounts/views.py` bugs (duplicate `is_following`)
- [ ] Review and fix `marketplace/models.py` indentation errors
- [ ] Remove Venv from git tracking
- [ ] Add `requirements.txt` with all dependencies
- [ ] Add `.gitignore`

### Phase 2: Accounts Module Complete (Week 2)
**Goal:** Full auth with all roles, profiles, password reset

- [ ] Add `django-allauth` for social auth / email verification
- [ ] Add NGO model + serializers
- [ ] Add Cooperative model + serializers
- [ ] Create DRF serializers for Profile
- [ ] Create Accounts API views (register, profile CRUD)
- [ ] Add farmer/buyer/ngo-specific registration endpoints
- [ ] Add password reset via email
- [ ] Add email verification flow
- [ ] Write unit tests for auth flows

### Phase 3: Marketplace Upgrade (Week 3)
**Goal:** Full marketplace with categories, filtering, images

- [ ] Create Category model + admin
- [ ] Migrate Product.category from CharField to FK to Category
- [ ] Add marketplace DRF serializers
- [ ] Create marketplace API views (list, detail, create, update, delete)
- [ ] Add search, filter, sort, pagination
- [ ] Add multiple image upload support
- [ ] Add product verification workflow
- [ ] Add farmer store API

### Phase 4: Orders & Cart (Week 4)
**Goal:** Complete order lifecycle

- [ ] Create orders app + Cart/CartItem models
- [ ] Migrate Order model from marketplace to orders
- [ ] Create OrderItem model (support multiple products per order)
- [ ] Create Cart API views
- [ ] Create Checkout API
- [ ] Create Order lifecycle API (status updates)
- [ ] Add OrderStatusLog for audit trail
- [ ] Add farmer order management

### Phase 5: Messaging & Notifications (Week 5)
**Goal:** Internal messaging system

- [ ] Create messaging app + Conversation model
- [ ] Migrate Message from marketplace to messaging
- [ ] Create Conversation API views
- [ ] Create Message API views
- [ ] Add real-time notification signals
- [ ] Create Notification model + views
- [ ] Add unread badge endpoint

### Phase 6: Dashboards (Week 6)
**Goal:** Role-specific analytics dashboards

- [ ] Create dashboard app
- [ ] Farmer dashboard stats (products, orders, revenue, followers)
- [ ] Buyer dashboard stats (orders, spend, wishlist, suppliers)
- [ ] NGO dashboard stats (recoveries, donations, impact)
- [ ] Admin dashboard stats (users, orders, verification queue)

### Phase 7: Additional Modules (Week 7-8)
**Goal:** Blog, Contact, Innovation, Recovery

- [ ] Create blog app with categories, posts, comments
- [ ] Create contact app with contact form
- [ ] Create innovation app with ideas, votes, comments
- [ ] Create recovery app with listings, claims, donations

### Phase 8: Frontend Integration & Polish (Week 9)
**Goal:** Wire frontend to real API data

- [ ] Update frontend HTML to fetch from API
- [ ] Add loading states and error handling
- [ ] Add JWT token management in frontend
- [ ] Create reusable API client JavaScript
- [ ] Test all flows end-to-end
- [ ] Performance optimization

---

## 8. Data Relationships

```
User ──1:1──> Profile
User ──1:N──> Product (as farmer)
User ──1:N──> Order (as buyer)
User ──1:N──> Order (as farmer)
User ──1:N──> Message (as sender)
User ──1:N──> Message (as recipient)
User ──M:N──> User (via FarmerFollow)
User ──1:N──> Cart
User ──1:N──> Review
User ──1:N──> Wishlist
User ──1:N──> Notification
User ──1:N──> BlogPost (as author)
User ──1:N──> InnovationIdea
User ──1:N──> RecoveryListing (as donor)
User ──1:N──> DonationClaim (as claimant)

Profile ──1:1──> Cooperative (optional)
Profile ──1:1──> NGO (optional)

Category ──1:N──> Product
Product ──1:N──> ProductImage
Product ──1:N──> Review
Product ──1:N──> OrderItem
Product ──1:N──> Wishlist
Product ──1:N──> CartItem

Cart ──1:N──> CartItem
Cart ──1:1──> Order (on checkout)

Order ──1:N──> OrderItem
Order ──1:N──> OrderStatusLog
Order ──1:1──> Payment (future)

Conversation ──M:N──> User (participants)
Conversation ──1:N──> Message
Conversation ──N:1──> Product (optional)

BlogCategory ──1:N──> BlogPost
BlogPost ──1:N──> BlogComment

InnovationIdea ──1:N──> InnovationVote
InnovationIdea ──1:N──> InnovationComment

RecoveryListing ──1:N──> DonationClaim
```

---

## 9. Security & Configuration

### Environment Variables (.env)
```ini
SECRET_KEY=django-insecure-...
DEBUG=True
DB_NAME=smartsave_db
DB_USER=root
DB_PASSWORD=***
DB_HOST=localhost
DB_PORT=3306
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:8000
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=***
DEFAULT_FROM_EMAIL=noreply@smartsave.rw
SITE_URL=http://localhost:8000
```

### Authentication Flow
```
1. User submits credentials → POST /api/auth/login/
2. Server validates → Returns access_token + refresh_token
3. Frontend stores tokens in localStorage
4. Every API call includes: Authorization: Bearer <access_token>
5. Access token expires (15 min) → Use refresh token to get new
6. On logout → Tokens discarded, blacklist option

Registration: Create User → Create Profile → Auto-login → Redirect
```

### Middleware Stack (recommended)
```
django.middleware.security.SecurityMiddleware
django.contrib.sessions.middleware.SessionMiddleware
corsheaders.middleware.CorsMiddleware          # ADD
django.middleware.common.CommonMiddleware
django.middleware.csrf.CsrfViewMiddleware
django.contrib.auth.middleware.AuthenticationMiddleware
django.contrib.messages.middleware.MessageMiddleware
django.middleware.clickjacking.XFrameOptionsMiddleware
```

### Installed Apps (target)
```python
INSTALLED_APPS = [
    # Django built-in
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    
    # Local apps
    'accounts',
    'marketplace',
    'orders',           # NEW
    'messaging',        # NEW
    'notifications',    # NEW
    'blog',             # NEW
    'contact',          # NEW
    'innovation',       # NEW
    'recovery',         # NEW
    'dashboard',        # NEW
    'payments',         # FUTURE
]
```

### DRF Settings
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 24,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

---

## Appendix: Key Code Improvements Needed

### Bugs Found in Current Code

1. **`accounts/models.py` (line 159–178):** `store_slug` slug generation logic. The `slug` variable is only assigned inside the `if not self.store_slug` block, but `self.store_slug = slug` on line 176 is outside? No — actually the `slug = base_slug` is inside the if. OK, it's fine. But the while loop logic could be cleaned up.

2. **`accounts/views.py` (line 176–184):** `is_following` is assigned twice — once on line 159 and again on line 176. The first assignment on line 159 is redundant and should be removed.

3. **`marketplace/models.py` (line 223–227):** `class Meta:` under `ProductImage` is at wrong indentation level. It should be inside the class.

4. **`marketplace/models.py` (line 362–377):** `Message` model has duplicated fields (`views`, `is_featured`, `is_active`, `slug`, `updated_at`) that clearly belong to `Product`, not `Message`. These are copy-paste errors and should be removed from Message model.

5. **`marketplace/views.py` (line 1):** `from decimal import Decimal` — correct and used properly.

6. **`core/urls.py` (line 48–49):** `static()` URL config in DEBUG mode — correct.

7. **`core/views.py`:** `serve_static_page` — simple but effective for initial static HTML serving. Will be replaced by API views.

### Frontend-Backend Alignment Checklist

- [ ] `index.html` stats → hardcoded → need `/api/home/stats/`
- [ ] `marketplace.html` products → static HTML → need `/api/marketplace/`
- [ ] `marketplace-product.html` details → static → need `/api/marketplace/{slug}/`
- [ ] All registration forms → POST to API instead of Django form POST
- [ ] `buyer-dashboard.html` → all data hardcoded → need multiple API calls
- [ ] `farmer-profile.html` → hardcoded data → need `/api/accounts/farmers/{slug}/`
- [ ] `cooperative-profile.html` → hardcoded → need `/api/accounts/cooperatives/{slug}/`
- [ ] `innovation.html` → hardcoded → need `/api/innovation/`
- [ ] `recovery.html` → hardcoded → need `/api/recovery/`
- [ ] `blog.html` / `blog-post.html` → hardcoded → need `/api/blog/`

---

> **This blueprint is a living document. Update it as requirements evolve.**
> 
> Next Step: Begin Phase 1 — Foundation Stabilization

Testing Render deployment
