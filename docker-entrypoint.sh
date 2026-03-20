#!/bin/sh

set -e

echo "🚀 Starting Hera Logistics SMS System..."

# Optional: skip DB wait (recommended for Render)
if [ "$SKIP_DB_WAIT" != "true" ]; then
    echo "⏳ Waiting for database..."
    sleep 2
fi

# Run migrations
echo "🔄 Running migrations..."
python manage.py migrate --noinput

# Optional superuser creation
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "👤 Creating superuser..."
    python manage.py createsuperuser --noinput || true
fi

# Skip static collection (already done at build)
if [ "$COLLECT_STATIC" != "false" ]; then
    echo "📦 Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "✅ Startup complete. Launching server..."

# Start app
exec "$@"