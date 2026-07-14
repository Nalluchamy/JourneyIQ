# SaaS Production Hardening — JourneyIQ v1.5.0

This guide details the security configurations, connection pool optimization, and asset management standards for deploying JourneyIQ to production.

---

## 1. Security Hardening

JourneyIQ implements standard SaaS security conventions.

### HTTPS & Transport Security
- **Enforced SSL**: Direct database connections to Supabase PostgreSQL require SSL (`sslmode=require`).
- **Secure Cookies**: JWT Refresh cookies are issued with `secure=True`, `httponly=True`, and `samesite="lax"`.
- **HSTS Headers**: The frontend vercel config and backend Nginx proxy enforce HTTP Strict Transport Security (`max-age=63072000; includeSubDomains; preload`).

### Secure HTTP Headers
 FastAPIs `SecurityHeadersMiddleware` injects the following headers into all outgoing responses:
- `Content-Security-Policy`: Restricts scripts and frames (`default-src 'self'; frame-ancestors 'none';`).
- `X-Frame-Options`: Denies clickjacking attempts (`DENY`).
- `X-Content-Type-Options`: Enforces strict MIME types (`nosniff`).
- `Referrer-Policy`: Restricts cross-origin leaks (`strict-origin-when-cross-origin`).
- `X-XSS-Protection`: Enables browser filtering (`1; mode=block`).

---

## 2. Database Connection Pooling

Connection parameters are optimized for Supabase transaction poolers:
- **Pool Size**: `20` concurrent active connections.
- **Max Overflow**: `10` extra overflow connections.
- **Pre-Ping**: `pool_pre_ping=True` checks connection liveness before executing queries to prevent stale connection errors.
- **Recycle Limit**: Connections are recycled every hour (`pool_recycle=3600`) to prevent database side leaks.

---

## 3. Storage & Asset Management

JourneyIQ leverages Supabase Storage to serve static product resources securely.

### Public Assets
- The `products` bucket contains static catalogs, variants, and product screenshots.
- Product images are served via a public CDN:
  `https://[project-ref].supabase.co/storage/v1/object/public/products/images/products/[image-name].png`

### Private Assets
- Customer logs, invoice summaries, and diagnostic reports are placed in a private storage folder.
- Endpoint controllers generate secure, temp signed URLs (expires in 1 hour) using the Storage API:
  `POST /storage/v1/object/sign/products/invoices/inv-001.pdf`
