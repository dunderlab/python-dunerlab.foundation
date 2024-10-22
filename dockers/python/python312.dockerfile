# Usar una imagen base de Python 3.12
FROM python:3.12

LABEL image="dunderlab/python312"
LABEL version="1.2"
LABEL maintainer="yencardonaal@unal.edu.co"
LABEL description=""
LABEL project=""
LABEL documentation=""
LABEL license="BSD 2-Clause"

# Establecer un directorio de trabajo
WORKDIR /app

# Instalar cualquier dependencia necesaria.
ENV PIP_ROOT_USER_ACTION=ignore
RUN pip install --upgrade confluent-kafka \
                          docker \
                          numpy \
                          scipy \
                          matplotlib \
                          tornado \
                          flask \
                          mne \
                          jupyterlab \
                          ntplib \
                          requests \
                          cryptography \
                          fastapi \
                          uvicorn \
                          paramiko \
                          figurestream \
                          radiant-framework \
                          dunderlab-foundation \
                          dunderlab-timescaledbapp \
                          dunderlab-docs \
                          chaski-confluent==0.1a5 \
                          radiant-framework

# Configure NTP
RUN DEBIAN_FRONTEND=noninteractive apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y ntp
COPY ntp.conf /etc/ntpsec/
