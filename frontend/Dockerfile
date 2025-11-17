# Multi-stage build for React frontend

FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments (passed from docker-compose)
ARG VITE_API_BASE_URL
ARG VITE_WS_URL
ARG VITE_LIVEKIT_URL

# Build application
RUN npm run build

# Production stage with Nginx
FROM nginx:1.25-alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
