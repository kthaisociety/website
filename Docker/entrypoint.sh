#!/bin/sh

if [ -n "$PG_HOST" ]
then
    echo -n "Waiting for postgres..."

    while ! netcat -z $PG_HOST $PG_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

python manage.py flush --no-input
python manage.py migrate

exec "$@"
