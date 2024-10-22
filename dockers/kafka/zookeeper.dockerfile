# Usar la imagen base de Confluent para ZooKeeper
FROM confluentinc/cp-zookeeper:latest

LABEL image="dunderlab/zookeeper"
LABEL version="1.1"
LABEL maintainer="yencardonaal@unal.edu.co"
LABEL description=""
LABEL project=""
LABEL documentation=""
LABEL license="BSD 2-Clause"

# Definir la variable de entorno
ENV ZOOKEEPER_CLIENT_PORT=2181

# Exponer los puertos para ZooKeeper
EXPOSE 2181
