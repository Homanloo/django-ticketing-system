#!/bin/sh

set -e

echo "Waiting for database..."
# Wait for PostgreSQL to be ready
until nc -z db 5432; do
  echo "Database is unavailable - sleeping"
  sleep 1
done
echo "Database is ready"

echo "Making migrations"
python manage.py makemigrations --noinput

echo "Running migrations"
python manage.py migrate --noinput

echo "Collecting static files"
python manage.py collectstatic --noinput

echo "Starting server"
exec "$@"

