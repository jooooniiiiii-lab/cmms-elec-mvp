FROM python:3.12-slim

WORKDIR /app

# Install system deps for CustomTkinter (display, fonts, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libx11-6 \
    libxcb1 \
    libxkbcommon0 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxrender1 \
    libxxf86vm1 \
    libgl1-mesa-glx \
    libegl1-mesa \
    libdbus-1-3 \
    libpango-1.0-0 \
    libcairo2 \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Volume for persistent config & DB
VOLUME ["/app/config.json", "/app/local_factory.db"]

# X11 display forwarding (host must have X server running)
ENV DISPLAY=${DISPLAY:-:0}

ENTRYPOINT ["python", "main.py"]
