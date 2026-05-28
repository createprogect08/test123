# ── Stage 1: Build ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY marisa-auth-frontend/package*.json ./
RUN npm ci --legacy-peer-deps

COPY marisa-auth-frontend/ .
RUN npm run build -- --configuration production

# ── Stage 2: Serve with Nginx ────────────────────────────────────────────────
FROM nginx:1.27-alpine

COPY --from=builder /app/dist/marisa-auth-frontend/browser /usr/share/nginx/html

# SPA fallback: tutte le route tornano a index.html
COPY nginx-spa.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
