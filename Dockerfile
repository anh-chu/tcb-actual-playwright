FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# Install X11 + VNC tooling
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    fluxbox \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# VNC configuration
ENV DISPLAY=:99
EXPOSE 5900

# Start Xvfb, window manager, VNC, then your app
CMD bash -c "\
    Xvfb :99 -screen 0 1920x1080x24 & \
    fluxbox & \
    x11vnc -display :99 -nopw -forever -shared -rfbport 5900 & \
    python main.py \
"
