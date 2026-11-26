# syntax=docker/dockerfile:1

# ---- Build stage: install exact lockfile dependencies and build static assets ----
FROM node:24-alpine@sha256:116b800c3754b440ee0aa3ed2f20f5bf3d99a554bfd9adeea09ea8017f6e85f5 AS build

WORKDIR /app

# Copy only the manifests first so the dependency layer is cached between builds.
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY index.html vite.config.js ./
COPY src ./src

# VITE_API_BASE_URL is intentionally unset: the app then calls its own origin,
# and Nginx proxies /api/ to the backend. No localhost URLs are baked in.
RUN npm run build

# ---- Production stage: serve static files with non-root Nginx ----
FROM nginxinc/nginx-unprivileged:1.29-alpine@sha256:0c79d56aee561a1d81c63f00eee5fb5fe29279560cdc55e91425133104c7fbe6 AS production

LABEL org.opencontainers.image.title="devopsmart-frontend" \
      org.opencontainers.image.description="DevOpsMart React storefront served by Nginx" \
      org.opencontainers.image.version="0.1.0"

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

# The base image already runs as the unprivileged "nginx" user (UID 101).
USER 101

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
