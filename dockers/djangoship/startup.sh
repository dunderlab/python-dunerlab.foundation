#!/bin/bash

rm -rf /app/djangoship/djangoship
mkdir /app/djangoship/djangoship

cp /etc/djangoship/django.conf.template  /etc/djangoship/django.conf
sed -i "s/{project}/${DJANGOPROJECT}/g" /etc/djangoship/django.conf

mkdir /etc/httpd/conf.d/
cp /etc/djangoship/django.conf /etc/httpd/conf.d/

echo 'LoadModule wsgi_module "/app/venv_python/lib/python3.12/site-packages/mod_wsgi/server/mod_wsgi-py311.cpython-311-x86_64-linux-gnu.so"' >> /etc/httpd/conf/httpd.conf
echo 'WSGIPythonHome "/app/venv_python"' >> /etc/httpd/conf/httpd.conf
echo "LoadModule deflate_module modules/mod_deflate.so" >> /etc/httpd/conf/httpd.conf
echo "LoadModule expires_module modules/mod_expires.so" >> /etc/httpd/conf/httpd.conf
echo "Include conf.d/*.conf" >> /etc/httpd/conf/httpd.conf

source /app/venv_python/bin/activate
if [ -f "/app/djangoship/requirements.txt" ]; then
    pip install --no-cache-dir -r /app/djangoship/requirements.txt
fi

cd /app/djangoship
if [ -f "./startup.sh" ]; then
    . ./startup.sh
fi

ntpd
httpd -D FOREGROUND
