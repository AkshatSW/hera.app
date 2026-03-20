# Dockerfile for Hera Logistics SMS System
FROM python:3.12-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Project files
COPY . .

# Entrypoint
COPY docker-entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Collect static at build time
RUN DJANGO_SECRET_KEY=build-secret python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

# ✅ FIXED CMD
CMD ["gunicorn", "config.wsgi:application"]