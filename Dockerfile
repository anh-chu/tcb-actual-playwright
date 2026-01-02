# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Runtime
FROM mcr.microsoft.com/playwright/python:v1.57.0-noble

# Install X11 tooling (Xvfb is enough for screenshots)
RUN apt-get update && apt-get install -y \
    xvfb \
    net-tools \
    x11-utils \
    && rm -rf /var/lib/apt/lists/*

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

# VNC and Web Port
EXPOSE 8000 6080

ENV DISPLAY=:99

CMD ["./entrypoint.sh"]
