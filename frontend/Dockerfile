# Stage 1: Build React SPA assets
FROM node:20-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve built assets via NGINX
FROM nginx:1.25-alpine

# Copy built HTML/JS/CSS assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy NGINX configuration
COPY ../nginx/nginx.conf /etc/nginx/nginx.conf

# Expose HTTP and HTTPS ports
EXPOSE 80 443

# Healthcheck probe using Alpine's wget
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
