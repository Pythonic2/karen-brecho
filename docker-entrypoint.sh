#!/bin/sh
set -eu

mkdir -p /app/data /app/media /app/staticfiles
cp -rn /app/media_defaults/. /app/media/

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
