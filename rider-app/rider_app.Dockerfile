FROM node:20-alpine AS builder
WORKDIR /app
COPY rider-app/package*.json ./
RUN npm ci --legacy-peer-deps
COPY rider-app/ ./
RUN npm run build -- --configuration production

FROM nginx:1.27-alpine
COPY --from=builder /app/dist/rider-app/browser /usr/share/nginx/html
COPY rider-app/nginx-rider.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
