# Kaku Craft — Backend Features

Complete feature inventory for the Django REST API backend.

**Stack:** Django 5.x · Django REST Framework · SimpleJWT · Channels · Celery · SQLite (default) · OpenAPI (drf-spectacular)

**Docs:** `/api/docs/swagger/` · `/api/docs/redoc/` · `/api/schema/`

---

## 1. Auth & Users (`/api/users/`)

- Email-based signup and signin
- JWT access + refresh tokens
- Roles: `customer`, `admin`, `super_admin` (role claim included in JWT)
- Authenticated profile retrieval
- Profile update with avatar upload
- Change password
- Custom user model (email as username)
- Django admin registration for user management

| Endpoint | Purpose |
|---|---|
| `POST /api/users/auth/signup/` | Register |
| `POST /api/users/auth/signin/` | Login (JWT) |
| `POST /api/users/auth/refresh/` | Refresh token |
| `GET /api/users/profile/` | Current user profile |
| `PATCH /api/users/profile/edit/` | Update profile / avatar |
| `POST /api/users/profile/change-password/` | Change password |

---

## 2. Product Catalog (`/api/products/`)

- Categories (name, slug, description, active)
- Products (name, slug, description, price, size, status, social links JSON)
- Multi-image product media
- Dynamic social media links (Instagram, TikTok, etc.) with format validation
- Public list + detail
- Filtering by category and min/max price
- Search by name/description
- Sorting by newest / price / popularity
- Admin-only category and product CRUD
- Admin product image upload and delete

| Endpoint | Purpose |
|---|---|
| `/api/products/categories/` | Category list / admin CRUD |
| `/api/products/items/` | Product list / admin CRUD |
| `/api/products/items/<slug>/` | Product detail / update / delete |
| `/api/products/items/<slug>/images/` | Upload images |
| `/api/products/items/<slug>/images/<id>/` | Delete image |

---

## 3. Cart & Standard Orders (`/api/orders/`)

### Cart
- Per-user cart
- Add item, update quantity, remove item
- Cart summary with totals and item count

### Standard orders
- Create order from cart
- Purchase-time price snapshots on line items
- Order statuses:
  - `pending_payment`
  - `payment_submitted`
  - `payment_verified`
  - `in_progress`
  - `delivered`
  - `completed`
  - `cancelled`
- Payment tracking: `total_price`, `amount_paid`, remaining amount, deposit required
- **50% deposit rule** before production (`has_minimum_deposit`)
- Customer payment proof upload (deposit + remaining on delivery)
- Admin payment proof approve / reject (reject rolls back to pending payment)
- Customer list / detail own orders
- Admin list / filter by status and guarded status updates

| Endpoint | Purpose |
|---|---|
| `GET /api/orders/cart/` | View cart |
| `POST /api/orders/cart/items/` | Add to cart |
| `/api/orders/cart/items/<id>/` | Update / remove cart item |
| `GET|POST /api/orders/` | List / create orders |
| `GET /api/orders/<id>/` | Order detail |
| `POST /api/orders/<id>/payment-proofs/` | Upload payment proof |
| `POST /api/orders/payment-proofs/<id>/review/` | Admin review proof |
| `PATCH /api/orders/<id>/status/` | Admin status update |

---

## 4. Custom Crochet Orders (`/api/orders/custom/`)

- Customer submits custom request (description + reference image)
- List / detail own custom requests
- Admin approve or reject
- Admin sets quoted price
- Customer confirms quote
- Custom payment proofs (same 50% deposit pattern)
- Admin payment review
- Admin production status updates

| Endpoint | Purpose |
|---|---|
| `GET|POST /api/orders/custom/` | List / submit custom order |
| `GET /api/orders/custom/<id>/` | Custom order detail |
| `POST /api/orders/custom/<id>/decision/` | Admin approve / reject |
| `POST /api/orders/custom/<id>/quote/` | Admin set quote |
| `POST /api/orders/custom/<id>/confirm/` | Customer confirm quote |
| `POST /api/orders/custom/<id>/payment-proofs/` | Upload payment proof |
| `POST /api/orders/custom/payment-proofs/<id>/review/` | Admin review proof |
| `PATCH /api/orders/custom/<id>/status/` | Admin status update |

---

## 5. Reviews & Wishlist (`/api/reviews/`)

### Wishlist
- Add / remove / list wishlist items
- Unique user–product pairing

### Reviews
- Rating + text reviews
- Purchase-validated (completed orders only)
- One review per product per order
- Customer submit / edit
- Public list of approved reviews
- Admin moderation flags

| Endpoint | Purpose |
|---|---|
| `GET|POST /api/reviews/wishlist/` | List / add wishlist |
| `DELETE /api/reviews/wishlist/<product_id>/` | Remove from wishlist |
| `GET|POST /api/reviews/` | List / create reviews |
| `/api/reviews/<id>/` | Review detail / edit |
| `POST /api/reviews/<id>/moderate/` | Admin moderation |

---

## 6. Messaging (`/api/messaging/` + WebSocket)

- Conversations linked to a standard order, custom order, or general support
- Create / list / detail conversations
- Send and list messages
- Mark conversation as read
- Admin close conversation
- Real-time WebSocket chat: `ws/chat/<conversation_id>/?token=<jwt>`
- Channel layer: in-memory by default; Redis when `REDIS_URL` is set

| Endpoint | Purpose |
|---|---|
| `GET|POST /api/messaging/conversations/` | List / create |
| `GET /api/messaging/conversations/<id>/` | Detail |
| `GET|POST /api/messaging/conversations/<id>/messages/` | List / send messages |
| `POST /api/messaging/conversations/<id>/read/` | Mark read |
| `POST /api/messaging/conversations/<id>/close/` | Admin close |

---

## 7. Notifications & Telegram (`/api/notifications/`)

- In-app notification center
- Event-driven notifications for orders, payments, custom orders, and messages
- Mark one / mark all as read
- Telegram account linking via deep-link token
- Telegram webhook (`/start <token>`) activation
- Celery task delivery when `TELEGRAM_BOT_TOKEN` is configured
- Eager Celery mode in DEBUG for local development

| Endpoint | Purpose |
|---|---|
| `GET /api/notifications/` | List notifications |
| `POST /api/notifications/<id>/read/` | Mark one read |
| `POST /api/notifications/read-all/` | Mark all read |
| `GET /api/notifications/telegram/link/` | Get / create link token |
| `POST /api/notifications/telegram/webhook/` | Telegram webhook |

---

## 8. CMS, Analytics & Assistant (`/api/cms/`)

### CMS
- Site content sections: homepage, about, contact, banners, social, FAQ
- Public read + admin write
- FAQ entries with seed management command (`seed_faqs`)

### Analytics (admin)
- Totals (revenue, orders, users, etc.)
- Timeseries data
- Popular products
- Pending custom orders
- Ranges: weekly / monthly / yearly / custom

### Assistant
- FAQ keyword-retrieval chatbot at `/api/cms/assistant/ask/`
- (Vector DB / Pinecone optional future upgrade)

| Endpoint | Purpose |
|---|---|
| `GET|POST /api/cms/content/` | List / create site content |
| `/api/cms/content/<key>/` | Content detail / update |
| `GET|POST /api/cms/faqs/` | FAQ list / create |
| `/api/cms/faqs/<id>/` | FAQ detail / update / delete |
| `GET /api/cms/analytics/` | Admin analytics |
| `POST /api/cms/assistant/ask/` | Ask assistant |

---

## 9. Platform & Infrastructure

- OpenAPI schema, Swagger UI, and ReDoc
- Django admin site
- Media uploads (`MEDIA_URL` / `MEDIA_ROOT`)
- Shared image upload validators and upload size limits
- CORS configuration for frontend
- DRF throttling (anon + authenticated rates)
- Production security flags when `DJANGO_DEBUG=false` (HSTS, secure cookies, SSL redirect)
- Env-based config (secrets, hosts, CORS, Redis, Celery, Telegram)
- ASGI via Daphne / Channels for HTTP + WebSockets
- Celery async task runner
- Role-based permissions and object ownership checks
- Automated pytest coverage across users, products, orders, reviews, messaging, notifications, and CMS

---

## App Map

| App | Responsibility |
|---|---|
| `users` | Auth, profiles, roles |
| `products` | Categories, catalog, images |
| `orders` | Cart, standard orders, custom orders, payments |
| `reviews` | Wishlist, ratings, moderation |
| `messaging` | Conversations, messages, WebSockets |
| `notifications` | In-app alerts, Telegram |
| `cms` | Site content, FAQs, analytics, assistant |
| `common` | Shared validators |
| `config` | Settings, URLs, ASGI/WSGI, Celery |
