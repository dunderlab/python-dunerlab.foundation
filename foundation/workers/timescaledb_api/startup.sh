#!/bin/bash

python manage.py collectstatic --noinput
python manage.py migrate
python manage.py makemigrations timescaledbapp
python manage.py migrate timescaledbapp --database=timescaledb
python manage.py create_groups

chown http -R /app/djangoship/ 2>/dev/null
chown http -R /app/djangorun/ 2>/dev/null
#python manage.py createsuperuser --username=yeison --email=yencardonaal@unal.edu.co
