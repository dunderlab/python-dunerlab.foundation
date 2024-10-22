import pickle

from confluent_kafka import Consumer, KafkaError

from dunderlab.api.utils import JSON
from dunderlab.api import aioAPI as API
from dunderlab.api.utils import get_data

conf = {
    'bootstrap.servers': 'kafka-logs-service:9093',
    'group.id': 'api',
    'auto.offset.reset': 'latest',
}

TOKEN = {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcyNTIyODA1OSwiaWF0IjoxNjkzNjkyMDU5LCJqdGkiOiIyMjg3Zjc2MTk5MDY0MzJiYTc0ZTZiMWQ4NWNiYzBiNCIsInVzZXJfaWQiOjF9.6wq-irScHTJ8nf8U0ruByrrYiEvEkqAbZFKTyF_A8Yc",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjkzNzc4NDU5LCJpYXQiOjE2OTM2OTIwNTksImp0aSI6ImRhZDgzNTU3NTk3MDQ3YzA5NDZhZWQ1OTczZmU5OWNkIiwidXNlcl9pZCI6MX0.RcO7-ms8tj8F-9JkOzfACYMhtByi7BKspOla7bhpAK0"
}

api = API('http://timescaledb-api-worker/timescaledbapp/', token=TOKEN['access'])

consumer = Consumer(conf)
consumer.subscribe(['timescaledb-api'])


# ----------------------------------------------------------------------
def write_on_api(data):
    """"""
    global api

    endpoint = data['endpoint']
    params = data['params']
    await getattr(api, endpoint).post(params)


try:
    while True:
        msg = consumer.poll(timeout=1)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                print(f'Final del stream en el topic/partición: {msg.topic()}/{msg.partition()}')
            else:
                print(f'Error al recibir el mensaje: {msg.error()}')
        else:
            data = pickle.loads(msg.value())
            write_on_api(data)
except KeyboardInterrupt:
    pass
finally:
    consumer.close()
