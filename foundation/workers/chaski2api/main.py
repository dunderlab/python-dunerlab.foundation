import asyncio

from dunderlab.api import aioAPI as API
from chaski.streamer import ChaskiStreamer

TOKEN = {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcyNTIyODA1OSwiaWF0IjoxNjkzNjkyMDU5LCJqdGkiOiIyMjg3Zjc2MTk5MDY0MzJiYTc0ZTZiMWQ4NWNiYzBiNCIsInVzZXJfaWQiOjF9.6wq-irScHTJ8nf8U0ruByrrYiEvEkqAbZFKTyF_A8Yc",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjkzNzc4NDU5LCJpYXQiOjE2OTM2OTIwNTksImp0aSI6ImRhZDgzNTU3NTk3MDQ3YzA5NDZhZWQ1OTczZmU5OWNkIiwidXNlcl9pZCI6MX0.RcO7-ms8tj8F-9JkOzfACYMhtByi7BKspOla7bhpAK0"
}

api = API('http://timescaledb-api-worker/timescaledbapp/', token=TOKEN['access'])


# ----------------------------------------------------------------------
def write_on_api(data):
    """"""
    global api

    endpoint = data['endpoint']
    params = data['params']
    await getattr(api, endpoint).post(params)


# ----------------------------------------------------------------------
async def run():
    """"""
    consumer = ChaskiStreamer(
        ip='0.0.0.0',
        port=51113,
        name='Foundation Chaski TimeScaleDB-API',
        run=False,
        subscriptions=['timescaledb-api'],
    )

    await consumer.run()
    async with consumer as message_queue:
        async for incoming_message in message_queue:
            write_on_api(incoming_message.data)


asyncio.run(run())
