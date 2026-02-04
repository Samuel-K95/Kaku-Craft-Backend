# Week 1: Core Infrastructure & Standard Commerce

_Goal: Set up the full-stack environment, authentication, and the basic "Standard Product" sales
loop._
● **Day 1: Project Scaffolding & JWT Auth**
○ **Backend:** DRF setup, Custom User model (Customer vs. Admin), JWT
integration.
○ **Frontend:** Next.js (App Router), Tailwind, and Shadcn/UI setup.
● **Day 2: Database Modeling & Product Catalog**
○ **Models:** Products, Categories, Images, and Social Media Links.
○ **Features:** Product listing, Category/Price filtering, and Detail views.
● **Day 3: Standard Order & Cart Logic**
○ **Logic:** Cart management (Zustand/Context), Order creation, Total calculation.
○ **State:** Order status: Pending Payment.
● **Day 4: Media Handling & Payment Proofs**
○ **Integration:** S3 or Cloudinary for secure image uploads.
○ **Feature:** Customer "Upload Screenshot" flow for the 50% pre-payment.
● **Day 5: Admin Dashboard (Phase 1)**
○ **Feature:** Order management UI for Admins to view/verify payment screenshots
and update statuses.
● **Day 6-7: Profile Management & UI Refinement**
○ **Feature:** Order history, address/profile updates, and overall mobile-responsive
polish.

# Week 2: Custom Orders, Chat, & Telegram Integration

_Goal: Build the complex 10-step custom order flow and the real-time communication layer._
● **Day 8: Custom Crochet Request Flow**
○ **Backend:** CustomOrder models with reference image support.
○ **Frontend:** Multi-step submission form for custom items.
● **Day 9: Real-Time In-App Chat (WebSockets)**
○ **Backend:** Django Channels & Redis setup.
○ **Feature:** Linking chat rooms to specific Order IDs (Standard or Custom).
● **Day 10: Admin Quoting & Custom Statuses**
○ **Workflow:** Admin reviews custom request -> Sets price -> User pays deposit.
○ **Logic:** Handling the transition from Pending Review to Approved.
● **Day 11: Telegram Bot (Part A: Account Linking)**
○ **Integration:** python-telegram-bot setup.


```
○ Feature: Secure "Link Telegram" flow where users/admins opt-in via a unique
token/start command.
● Day 12: Telegram Bot (Part B: Notifications)
○ Async Logic: Celery tasks to push notifications to Telegram for: New orders,
Payment verification, and Message alerts.
● Day 13: Integrated Notification System
○ Logic: System-wide notification center (In-app Bell + Telegram Fallback).
● Day 14: Testing the "Communication Loop"
○ Stress test the flow from Custom Request -> Chat Clarification -> Telegram Alert
-> Payment.
```
# Week 3: AI Assistant, Analytics, & Final Polish

_Goal: Implement the RAG Chatbot, Admin insights, and finalize the CMS._
● **Day 15: Content Management System (CMS)**
○ **Feature:** Admin UI to update Home page sections, About content, and
Promotional banners without code changes.
● **Day 16: RAG Chatbot (Part A: Data Ingestion)**
○ **Setup:** Vector Database (Pinecone or local FAISS).
○ **Data:** Ingesting this documentation and FAQs into the knowledge base.
● **Day 17: RAG Chatbot (Part B: Frontend Integration)**
○ **Feature:** Floating AI assistant that answers questions about "How payments
work" and "Delivery timelines."
● **Day 18: Reviews, Ratings, & Wishlist**
○ **Logic:** Purchase-validated reviews (only after Completed status).
○ **Feature:** Wishlist persistence across sessions.
● **Day 19: Analytics & Reporting**
○ **Feature:** Admin charts showing Revenue, Total Orders, and Popular Products
(using Recharts).
● **Day 20: Performance Tuning & Security**
○ **Tasks:** Query optimization, async task monitoring, and ensuring secure media
access (Signed URLs).
● **Day 21: Deployment & QA**
○ **Deployment:** Vercel (Frontend), Railway/DigitalOcean (Backend/Worker/Redis).
○ **Final:** End-to-end "Happy Path" testing.


# Key Technical Considerations for this Plan

1. **Asynchronous Mastery:** Since the PDF emphasizes "Asynchronous by design," you
    must ensure that **Celery** is handling not just the Telegram bot, but also the image
    processing and the RAG document indexing to avoid blocking the API.
2. **The "50% Rule":** Your database needs separate fields for total_price and
    amount_paid. An order should only move to In Progress when amount_paid >=
    (total_price * 0.5).
3. **Telegram Webhook vs. Polling:** For a production app, use **Webhooks** for the Telegram
    bot to ensure immediate delivery of notifications and better scalability.
4. **Chat UI:** Ensure the In-App chat is "context-aware." If a user opens chat from a specific
    Custom Order page, the chat should automatically reference that order.


