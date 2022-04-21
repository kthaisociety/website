#!/bin/sh

echo "Updating repository..."
git checkout "$TYPE"
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
