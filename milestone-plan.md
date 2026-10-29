# Kaku Craft Backend Milestone Plan (Small Steps)

Source: [Kaku Platform.md](Kaku%20Platform.md)

## Status Legend
- Done: Implemented in current codebase
- Next: Small immediate milestone
- Pending: Not implemented yet

## Current Baseline (Already Implemented)

### M0. Project & API Foundation
Status: Done
- Django project scaffolded with app modularization (`users`, `products`, `orders`, `reviews`, `messaging`, `notifications`, `cms`)
- DRF added and configured
- OpenAPI/Swagger/ReDoc enabled via drf-spectacular
- JWT auth configured with SimpleJWT
- CORS configured for frontend integration
- Media settings enabled (`MEDIA_URL`, `MEDIA_ROOT`)
- Channels + Daphne ASGI for WebSockets
- Celery task runner (eager in DEBUG by default)

### M1. User Identity Core
Status: Done
- Custom `User` model using email as username
- Role model in place (`customer`, `admin`, `super_admin`)
- Signup/signin/refresh endpoints available
- Authenticated profile retrieval endpoint available
- Profile update endpoint with avatar upload available
- Change password endpoint available
- JWT token includes role claim
- Admin registration for user management available

## Milestone Breakdown (Small, Execution-Friendly)

### Phase A: Product Catalog

### M2. Product Category Model
Status: Done
- Add `Category` model (name, slug, description, active)
- Add category admin registration
- Add migration + seed-ready structure

### M3. Product Base Model
Status: Done
- Add `Product` model (name, slug, description, price, size, status)
- Link product to category
- Add `is_active` and ordering fields

### M4. Product Media & Social Links
Status: Done
- Add `ProductImage` model (multi-image support)
- Add dynamic social links field (JSON key/value)
- Validate accepted link formats
- Admin product image upload API (`/api/products/items/<slug>/images/`)

### M5. Product Read APIs
Status: Done
- Product list endpoint
- Product detail endpoint
- Category list endpoint

### M6. Product Filtering
Status: Done
- Filter by category
- Filter by min/max price
- Search by name/description
- Sort by newest/price/popularity

### M7. Product Admin CRUD
Status: Done
- Admin-only create/update/delete product APIs
- Admin-only category management APIs

### Phase 0/A Readiness Gate
Status: Done
- Automated pytest coverage for `users` and `products` flows
- Production hardening added in settings (env-based secrets/debug/hosts/CORS)
- DRF throttling defaults enabled
- Production-only security flags enabled when `DJANGO_DEBUG=false`
- Test media isolation enabled to keep repository clean

### Phase B: Cart + Standard Orders + 50% Payment Rule

### M8. Cart Model Layer
Status: Done
- `Cart` and `CartItem` models per user
- Quantity and per-item subtotal logic

### M9. Cart APIs
Status: Done
- Add to cart / update quantity / remove item / view cart summary

### M10. Order Core Models
Status: Done
- `Order` and `OrderItem` models with purchase-time price snapshots
- Statuses: pending_payment, payment_submitted, payment_verified, in_progress, delivered, completed (+ cancelled)

### M11. Payment Tracking Fields
Status: Done
- `total_price`, `amount_paid`, `remaining_amount`, `deposit_required`
- 50% deposit gate before production (`has_minimum_deposit`)

### M12. Payment Proof Upload
Status: Done
- `PaymentProof` model + customer upload endpoint locked to owned orders

### M13. Payment Verification Flow
Status: Done
- Admin approve/reject payment proof
- Status progression with rejection rollback to pending_payment

### M14. Remaining Payment Completion
Status: Done
- Remaining payment proof upload while delivered
- Completion when fully paid

### M15. Order APIs
Status: Done
- Customer: create from cart, list/detail own orders
- Admin: list/filter by status, guarded status updates

### Phase C: Custom Crochet Orders

### M16. Custom Order Model
Status: Done
- `CustomOrder` + `CustomOrderPaymentProof` with quote/payment/status fields

### M17. Custom Order APIs (Customer)
Status: Done
- Submit request, list/detail own requests, confirm quote, upload payment proof

### M18. Custom Order APIs (Admin)
Status: Done
- Approve/reject, set quote, review payments, move production statuses

### Phase D: Reviews & Wishlist

### M19. Wishlist Data Model
Status: Done
- `WishlistItem` with user-product uniqueness

### M20. Wishlist APIs
Status: Done
- Add/remove/list wishlist

### M21. Review Model Rules
Status: Done
- `Review` with rating/text/moderation flags
- One review per product per order; purchase-validated (completed orders only)

### M22. Review APIs
Status: Done
- Customer submit/edit; public approved list; admin moderation

### Phase E: Messaging, Notifications, Telegram (Async)

### M23. In-App Conversation Model
Status: Done
- `Conversation` + `Message` linked to Order/CustomOrder (or general support)

### M24. Messaging APIs (polling)
Status: Done
- List/create conversations, send/list messages, mark read, admin close

### M25. Real-Time Messaging Layer
Status: Done
- Django Channels WebSocket consumer at `ws/chat/<conversation_id>/?token=<jwt>`
- In-memory channel layer by default; Redis when `REDIS_URL` is set

### M26. Notification Core
Status: Done
- `Notification` model + event dispatch on commerce/message actions

### M27. Async Task Runner
Status: Done
- Celery integrated (`config/celery.py`); eager mode in DEBUG for local/tests

### M28. Telegram Link & Delivery
Status: Done
- `TelegramLink` + deep-link token API
- Webhook `/start <token>` activation
- Celery task delivery when bot token is configured

### Phase F: CMS, Analytics, RAG Assistant

### M29. CMS Content Models
Status: Done
- `SiteContent` for homepage/about/contact/banners/social/FAQ sections

### M30. CMS APIs
Status: Done
- Public read + admin write endpoints

### M31. Analytics Data Endpoints
Status: Done
- Totals + timeseries + popular products + pending custom orders
- Ranges: weekly/monthly/yearly/custom

### M32. Analytics Performance Pass
Status: Done
- Indexes on order/custom order status + created_at; aggregated queries

### M33. FAQ/RAG Data Pipeline
Status: Done
- `FAQEntry` model + `seed_faqs` management command

### M34. RAG API Endpoint
Status: Done
- Keyword-retrieval assistant at `/api/cms/assistant/ask/`
- (Vector DB/Pinecone optional future upgrade; current FAQ retriever is production-usable)

### Phase G: Quality, Security, and Release Hardening

### M35. Permission Hardening
Status: Done
- Role-based admin permissions + object ownership checks on cart/orders/chat/reviews

### M36. Test Coverage Baseline
Status: Done
- Tests for users, products, orders (50% rule), reviews/wishlist, messaging, notifications, CMS/assistant

### M37. Upload Security & Validation
Status: Done
- Image extension validators on payment/custom uploads
- Shared `common.validators.validate_image_upload` + upload size settings

### M38. Production Readiness
Status: Done
- Env-based secrets/debug/hosts/CORS/Redis/Celery/Telegram
- Logging configured; `.env.example` updated
- Note: still SQLite by default; swap DB engine via env for production deployments

---

## Suggested Build Order (Immediate)
1. ~~M2 -> M7 (Product catalog complete)~~
2. ~~M8 -> M15 (Cart + standard order + payment flow)~~
3. ~~M16 -> M18 (Custom order flow)~~
4. ~~M19 -> M22 (Wishlist + Reviews)~~
5. ~~M23 -> M28 (Messaging + notifications + Telegram)~~
6. ~~M29 -> M34 (CMS + Analytics + RAG)~~
7. ~~M35 -> M38 (Hardening + tests + release)~~

## Next Frontend Integration Priorities
1. Wire auth + product catalog to `/api/users` and `/api/products`
2. Cart/checkout against `/api/orders`
3. Custom order form + chat against `/api/orders/custom` and `/api/messaging`
4. Admin dashboard: payment verification, analytics, CMS
