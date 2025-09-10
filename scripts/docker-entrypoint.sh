#!/bin/sh
set -e

echo "Running Django migrations..."
python manage.py migrate --noinput

if [ -f setup_dev_admin_permissions.py ]; then
  echo "Running setup_dev_admin_permissions.py"
  python setup_dev_admin_permissions.py || true
fi

# Create a readiness marker on the shared project volume so other containers
# (celery-beat/worker) can wait for migrations to complete.
touch /app/.web_ready
echo "Web readiness marker created at /app/.web_ready"

echo "Starting Django development server"
exec python manage.py runserver 0.0.0.0:8000
