# Security Guidelines & hardening - JourneyIQ

JourneyIQ implements industry-standard enterprise security configurations to prevent vulnerabilities, protect customer data, and secure APIs.

## 1. Security Headers (`SecurityHeadersMiddleware`)
All HTTP responses carry strict security headers to prevent common browser-side exploits:
- **Content-Security-Policy (CSP)**: `default-src 'self'; frame-ancestors 'none'; object-src 'none';` - Restricts resource loading to verified origins and blocks clickjacking/object injections.
- **X-Frame-Options**: `DENY` - Prevents the application from being loaded in frames/iframes to mitigate Clickjacking.
- **X-Content-Type-Options**: `nosniff` - Prevents MIME-sniffing vulnerabilities.
- **Referrer-Policy**: `strict-origin-when-cross-origin` - Secures referrer header disclosure.

## 2. CORS Policy
Cross-Origin Resource Sharing (CORS) is restricted to designated frontend origins. Credentials transmission is allowed securely only for specified hosts.

## 3. Rate Limiting Configurations
Sliding-window rate limits are enforced per-client (IP + User ID context):
- **Authentication Endpoints**: 5 requests per minute.
- **AI Recommendation APIs**: 60 requests per minute.
- **Business/Analytics Dashboards**: 120 requests per minute.
- **All other public APIs**: 100 requests per minute.

## 4. Input Sanitization
The utility `app/utils/sanitization.py` automatically strips raw HTML tags, inline scripts (`<script>`), and object identifiers from user inputs (e.g. shipping address forms) to eliminate Cross-Site Scripting (XSS).

## 5. Dependency Audit & Scanning
Dependency vulnerability audits run as part of CI checks.
- **Current status**: Up-to-date.
- **Exceptions**: `ecdsa 0.19.2` displays warning `PYSEC-2026-1325`. There is currently no upstream fix version available. This is accepted as a low-severity risk as the cryptography suite does not rely on vulnerable paths in standard JWT signatures.
