# Stage 1: Build Angular
FROM node:20-alpine AS builder
WORKDIR /app
COPY marisa-express-app/package*.json ./
RUN npm ci --legacy-peer-deps
COPY marisa-express-app/ ./
RUN npm run build -- --configuration=production

# Stage 2: Serve con Nginx
FROM nginx:1.27-alpine
COPY --from=builder /app/dist/marisa-express-app/browser /usr/share/nginx/html

RUN cat > /etc/nginx/conf.d/default.conf << 'NGINX'
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://marisa-express:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location ^~ /static/uploads/ {
        proxy_pass http://marisa-express:5000/static/uploads/;
        proxy_set_header Host $host;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX

EXPOSE 80
