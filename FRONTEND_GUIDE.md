# JourneyIQ Storefront Frontend Architecture Guide (Phase 4)

This document provides a comprehensive overview of the customer-facing storefront built in Phase 4 of the JourneyIQ platform. It outlines the application routing, state management, API services client wrapper, real-time event tracking system, and test structures.

---

## 1. Application Pages

The storefront comprises 7 highly polished pages styled dynamically under the platform's dark-mode color scheme:

1.  **Home Page (`/`)**: Displays introductory copy highlighting capabilities alongside quick actions to browse the catalog.
2.  **Products Catalog (`/products`)**: The principal storefront interface containing:
    *   A live debounced search input.
    *   A multi-parameter filter sidebar (Category, Brand, Price Range, and Stock Availability status).
    *   Sorting controls (Newest first, Price: Low to High, Price: High to Low, Stock capacity).
    *   Paginated product cards showing ratings, pricing, brand tags, and stock indicators.
    *   Direct interactive overlays for "Add to Cart" and "Add to Wishlist".
3.  **Product Details (`/products/:id`)**: Shows full product specifics, a tabbed reviews list, a purchaser-verified star rating feedback form, related recommendations, and a recently viewed product list.
4.  **Wishlist Page (`/wishlist`)**: Displays items saved by the customer, offering quick actions to move a product directly to the shopping cart or remove it.
5.  **Shopping Cart Page (`/cart`)**: Summarizes items added for purchase, lets users increment/decrement quantities (verifying stock limits), clear the cart, and view a pricing invoice calculating Estimated Tax (8%) and Grand Totals.
6.  **Profile Settings (`/profile`)**: An authenticated page displaying user info, allowing edits to name or phone numbers, and loading a read-only list of past orders.
7.  **Authentication Tab-form (`/login`)**: Swappable glassmorphic Sign In / Sign Up panels saving session tokens.

---

## 2. Routing Structure

Routing is declared inside `frontend/src/App.tsx` using `react-router-dom`:

| Route Path | Page Component | Access Type | Description |
| :--- | :--- | :--- | :--- |
| `/` | `Home` | Public | Storefront Landing |
| `/products` | `Products` | Public | Catalog list with Search & Filters |
| `/products/:id` | `ProductDetails` | Public | Detailed views, reviews, related items |
| `/login` | `Login` | Public | Tabbed auth login/register panel |
| `/wishlist` | `Wishlist` | Protected | Saved items page (redirects if guest) |
| `/cart` | `Cart` | Protected | Shopping cart invoice summaries |
| `/profile` | `Profile` | Protected | Personal settings & orders list |

---

## 3. State Management & API Integration

The frontend utilizes a hybrid state management model combining browser cache persistence and global query state:

*   **Session Token Storage**: Access and Refresh tokens are persisted inside `localStorage`.
*   **Active Session Journey ID**: A random UUID v4 tracking token is generated on startup and cached inside `sessionStorage`.
*   **Global Server Cache**: Syncing is performed via **TanStack Query** (`@tanstack/react-query`), ensuring real-time header counts and badges remain synchronized across layout views when queries are invalidated on mutations.

### API Interceptor Headers (`src/services/api.ts`):
Every API call made by our unified `apiClient` automatically attaches credentials and tracing details:
```typescript
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  config.headers['X-Session-ID'] = sessionStorage.getItem('session_id');
  return config;
});
```

---

## 4. Real-time Event Tracking

storefront events are logged automatically inside database events tracking sheets. The tracking matches the following configuration:

| Event Type | Action Trigger | Logged By | Session Context |
| :--- | :--- | :--- | :--- |
| `homepage_view` | Opening the landing index route | Frontend hook | Guest or User UUID |
| `category_view` | Applying category filters on catalog | Frontend hook | Guest or User UUID |
| `search` | Entering search queries (debounced) | Frontend hook | Guest or User UUID |
| `product_view` | Accessing product details page | Frontend hook | Guest or User UUID |
| `wishlist_add` | Adding product to wishlist | Backend route | Logged User |
| `wishlist_remove`| Deleting product from wishlist | Backend route | Logged User |
| `cart_add` | Placing item into shopping cart | Backend route | Logged User |
| `cart_remove` | Deleting item from cart | Backend route | Logged User |
| `login` | Successful credentials verification | Backend route | Logged User |
| `logout` | Logging out and revoking token | Backend route | Logged User |
| `profile_update` | Updating profile name/phone fields | Backend route | Logged User |

---

## 5. Testing Summary

Automated validation covers core storefront features across 25 unit and integration test specs (`backend/tests/`):
*   **Cart Operations (`test_storefront_cart.py`)**: Asserts adding items, quantity updates, inventory capacity limits validations, and cart deletions.
*   **Wishlist Logs (`test_storefront_wishlist.py`)**: Asserts additions, removal, and unique constraints blocking duplicate saves.
*   **Purchase-Verified Reviews (`test_storefront_reviews.py`)**: Verifies ratings must be 1-5, public GET retrievals, and rejects reviews from non-purchasing users.
*   **Chronological Event Tracking (`test_storefront_events.py`)**: Asserts guests events, authenticated events, and unique recently viewed deduplications.
