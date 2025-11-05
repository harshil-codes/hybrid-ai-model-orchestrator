##########################################
# 🧱 Stage 1: Build the app using Node.js #
##########################################
FROM node:20-alpine AS build

# Create working directory
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy all app source code
COPY . .

# Build the static files (output in /app/dist by default)
RUN npm run build

##########################################
# 🧱 Stage 2: Serve the app with NGINX   #
##########################################
FROM nginx:1.25-alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built static assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom OpenShift-friendly NGINX configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create a writable directory for NGINX cache/temp files
RUN mkdir -p /tmp/nginx-cache && chmod -R 777 /tmp/nginx-cache

# Use a non-root user (required for OpenShift)
USER 1001

# Expose port 8080 (default for OpenShift routes)
EXPOSE 8080

# Start NGINX in foreground
CMD ["nginx", "-g", "daemon off;"]

