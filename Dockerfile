FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# HF Spaces run containers as non-root — create matching user
RUN useradd -m -u 1000 user

WORKDIR /app

# Copy dep file first for layer caching
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of app
COPY --chown=user . .

USER user

EXPOSE 7860
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:7860/ || exit 1

CMD ["python", "app.py"]
