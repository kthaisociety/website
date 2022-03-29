#!/bin/sh

echo "Updating repository..."
if [ "$TYPE" = "beta" ]; then
  git checkout beta
fi
git pull --rebase


if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! netcat -z $PG_HOST $PG_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

python manage.py flush --no-input
python manage.py migrate

exec "$@"
