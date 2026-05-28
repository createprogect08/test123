# Stage 1: Build Angular
FROM node:20-alpine AS builder
WORKDIR /app
COPY ristoratori-app/package*.json ./
RUN npm ci --legacy-peer-deps
COPY ristoratori-app/ ./
RUN npm run build -- --configuration production

# Stage 2: Serve con Nginx
FROM nginx:1.27-alpine
COPY --from=builder /app/dist/ristoratori-app/browser /usr/share/nginx/html
COPY ristoratori-app/nginx-ristoratori.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
