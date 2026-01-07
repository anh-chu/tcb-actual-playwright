# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Runtime
FROM mcr.microsoft.com/playwright/python:v1.57.0-noble

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --ignore-installed -r requirements.txt

# Copy App Code
COPY . .

# Copy Frontend Build from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Setup Entrypoint
RUN chmod +x entrypoint.sh

# Web Port
EXPOSE 8000

CMD ["./entrypoint.sh"]
