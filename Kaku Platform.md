# Kaku Craft Platform – Comprehensive System

# Documentation

## 1. Overview

Kaku Craft is a full‑stack e‑commerce platform designed for buying, selling, and custom‑ordering
crocheted products such as cardigans, dolls, toys, and related handmade items. The platform supports
both standard product purchases and custom crochet requests, with integrated messaging,
notifications, partial payment workflows, and an admin management dashboard.

The system is built using **Django Rest Framework (DRF)** as the backend API and **Next.js** as the
frontend client. The platform is asynchronous by design, allowing multiple features (chat, notifications,
order updates, uploads) to operate concurrently.

## 2. Actors & Roles

### 2.1 Customers (Users)

Customers are end users who browse products, place orders, request custom crochet items, chat with
the admin, and track order status.

### 2.2 Admin (Owner)

Admins manage the platform, approve custom orders, verify payments, manage users, moderate
content, and view analytics.

## 3. High‑Level System Architecture

```
Frontend: Next.js (App Router, Tailwind CSS)
Backend: Django Rest Framework
Authentication: JWT‑based authentication
Media Handling: Image uploads (products, payment proofs, custom orders)
Async Operations: Background tasks for notifications, messaging, and status updates
Chatbot: RAG‑based assistant for platform FAQs
```
## 4. Core Functional Modules

### 4.1 Authentication & User Management

```
User registration and login
JWT‑based session management
Role‑based access control (Customer vs Admin)
Profile management (name, email, avatar, order history)
```
#### • • • • • • • • • •


### 4.2 Product Catalog & Shopping

**Features**

```
Browse list of existing crochet products
Filter products by:
Category (toys, cardigans, dolls, etc.)
Price range
View product details
Add products to cart
Wishlist functionality
```
**Product Attributes**

```
Name
Description
Price
Category
Size
Images
Social media links (dynamic key‑value pairs):
Instagram
TikTok
Other platforms
```
### 4.3 Order & Payment Flow (Standard Products)

**Flow**

```
Customer adds product(s) to cart
Customer places an order
System calculates total price
Customer pays 50% pre‑payment
Customer uploads payment screenshot
Admin verifies payment proof
Order status updates
Remaining 50% paid upon delivery
```
**Order Statuses**

```
Pending Payment
Payment Submitted
Payment Verified
In Progress
Delivered
Completed
```
#### • • • • • • • • • • • • • • • • •

#### 1.

#### 2.

#### 3.

#### 4.

#### 5.

#### 6.

#### 7.

#### 8.

#### • • • • • •


### 4.4 Custom Crochet Orders

**Flow**

```
Customer uploads:
Reference image
Description
System creates a custom order request
Automatic in‑app message sent to admin with image & details
Admin and customer communicate via in‑app chat
Admin approves or rejects the request
Admin sets quoted price
Customer confirms and pays 50% pre‑payment
Remaining payment on delivery
```
**Statuses**

```
Pending Review
Approved
Rejected
In Progress
Completed
```
### 4.5 In‑App Chat & Messaging System

**Features**

```
Real‑time messaging between admin and users
Used for:
Custom order discussions
Order clarifications
Support
Chat is tied to:
Orders
Custom order requests
```
**Notifications**

```
Bot‑generated notifications when:
New message is received
Order status changes
Payment is verified
```
### 4.6 Notifications System

**Features**

```
In-app notifications for users and admins
Triggered on:
```
#### 1.

#### 2.

#### 3.

#### 4.

#### 5.

#### 6.

#### 7.

#### 8.

#### 9.

#### 10.

#### • • • • • • • • • • • • • • • • • • •


```
New messages
Order status changes
Payment verification
Custom order approval or rejection
Notifications are delivered asynchronously
```
**Telegram Bot Integration**

```
A Telegram bot is integrated as an additional notification channel
Users and admins can opt-in and link their Telegram account
Major events trigger Telegram notifications:
New order placed
Payment proof uploaded
Payment verified or rejected
New custom order request
Custom order approved or rejected
New in-app message received
```
Telegram notifications complement in-app notifications and ensure timely delivery even when users are
offline.

```
Message notifications
Order status updates
Custom order approval/rejection
Implemented asynchronously
```
### 4.7 Reviews & Ratings

```
Customers can leave reviews only if they have purchased the product
One review per product per order
Admin moderation capability
```
### 4.8 Wishlist

```
Customers can save products
Wishlist persists across sessions
```
### 4.9 Content Management System (CMS)

Admins can manage dynamic site content: - Home page sections - About page content - Contact details

- Social media links - Promotional banners

### 4.10 Admin Dashboard

**Capabilities**

```
User management
```
#### • • • • • • • • • • • • • • • • • • • • • • • •


```
Product management
Order & payment verification
Custom order approvals
Review moderation
Messaging with users
```
### 4.11 Analytics & Reporting

Admins can view statistics: - Weekly, monthly, yearly - Custom date ranges

Metrics include: - Total orders - Revenue - Popular products - Pending custom orders

Visualized using charts and reports

### 4.12 RAG‑Based Chatbot

```
Helps users ask questions about:
How payments work
Delivery timelines
Custom order process
Uses retrieval‑augmented generation based on platform documentation and FAQs
```
## 5. Use Cases Summary

### Customer Use Cases

```
Browse and filter products
Place standard orders
Request custom crochet items
Upload payment proofs
Track order status
Chat with admin
Receive in-app and Telegram notifications
Manage wishlist and profile
Leave reviews for purchased products
```
### Admin Use Cases

```
Manage users
Add and manage products
Verify payments
Approve or reject custom orders
Chat with customers
Receive Telegram alerts for major events
Control site content
View analytics and reports
```
#### • • • • • • • • • • • • • • • • • • • • • • • • • • •


### Telegram Bot Use Cases

```
Notify admins of new orders and payment submissions
Notify users of order status changes
Notify both parties of new chat messages
Serve as a fallback notification channel when users are offline
```
### Customer Use Cases

```
Browse and filter products
Place standard orders
Request custom crochet items
Upload payment proofs
Track order status
Chat with admin
Receive notifications
Leave reviews
```
### Admin Use Cases

```
Manage users
Add and manage products
Verify payments
Approve custom orders
Chat with customers
Control site content
View analytics and reports
```
## 6. Functional Requirements

```
User authentication and authorization
Product listing and filtering
Cart and wishlist management
Partial payment handling (50%)
Image uploads (products, custom orders, payment proofs)
In‑app chat and notifications
Admin dashboard and CMS
Review system with purchase validation
RAG chatbot support
```
## 7. Non‑Functional Requirements

### Performance

```
Async handling of messaging, notifications, and uploads
Scalable API endpoints
```
#### • • • • • • • • • • • • • • • • • • • • • • • • • • • • • •


### Security

```
JWT authentication
Role‑based access control
Secure media uploads
```
### Reliability

```
Consistent order and payment state management
```
### Usability

```
Mobile‑responsive UI
Clear order and payment status visibility
```
### Maintainability

```
Modular backend apps
Clear API contracts
```
## 8. Asynchronous System Behavior

The system is designed with asynchronous execution to support scalability and responsiveness.

Async functionality includes: - Real-time chat messaging - Background dispatch of in-app notifications -
Telegram bot notification delivery - Non-blocking file uploads (images, payment proofs) - Order status
updates without blocking user actions

Asynchronous tasks may be handled using background workers, message queues, or event-driven
patterns to ensure multiple features can operate concurrently.

The system supports asynchronous functionality to allow: - Real‑time chat - Background notification
dispatch - Concurrent order processing - Non‑blocking file uploads

Async tasks may be handled using background workers or event‑driven patterns.

## 9. Conclusion

Kaku Craft is a feature‑rich, role‑based, async‑enabled e‑commerce platform tailored for handmade
crochet products. It combines traditional shopping with custom order workflows, integrated messaging,
and intelligent assistance, providing a seamless experience for both customers and the business owner.

####


