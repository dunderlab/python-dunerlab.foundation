# Usar la imagen de base de Confluent
FROM confluentinc/cp-kafka:latest

LABEL image="dunderlab/kafka"
LABEL version="1.1"
LABEL maintainer="yencardonaal@unal.edu.co"
LABEL description=""
LABEL project=""
LABEL documentation=""
LABEL license="BSD 2-Clause"

# Definir la variable de entorno
ENV KAFKA_ZOOKEEPER_CONNECT=zookeeper-service:2181
ENV KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka-service:9092
ENV KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1

# Exponer los puertos para Kafka
EXPOSE 9092
