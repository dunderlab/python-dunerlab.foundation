#!/usr/bin/env python

from colorama import init
from colorama import Fore, Back
from chaski.streamer import ChaskiStreamer
import argparse
import logging
# from datetime import datetime

import asyncio

from foundation.utils import Workers

init(autoreset=True)

parser = argparse.ArgumentParser(description="Start an HCI logger.")
parser.add_argument(
    '-t',
    '--topic',
    action='append',
    default=['ALL'],
    help="Topics to be logged.",
)
parser.add_argument(
    '-l', '--loglevel', default='NOTSET', help="Set the logging level"
)
parser.add_argument(
    '-a', '--advertise_addr', default=None, help="Advertise address."
)

args = parser.parse_args()

logging.basicConfig()

workers = Workers(swarm_advertise_addr=args.advertise_addr)


# ----------------------------------------------------------------------
async def run():
    """"""

    consumer = ChaskiStreamer(
        subscriptions=['logs'], run=False
    )

    await consumer.connect('127.0.0.1', port=51114)
    asyncio.create_task(consumer.run())

    if args.topic == ['ALL']:
        topics = list(
            filter(
                lambda topic: not topic.startswith('__'),
                consumer.subscriptions,
            )
        )
        topics = topics + workers.swarm.services
    else:
        topics = args.topic

    if topics:
        consumer.subscribe(topics)
    print(Back.CYAN + Fore.BLACK + f'Topics: {", ".join(topics)}')

    async with consumer as message_queue:
        async for msg in message_queue:

            if not msg:
                continue

            if msg.topic == 'logs':
                print(msg.data)
                continue


            # print('+'+msg.data)

            msg = f'{msg.data.replace("@", ": ")}'

            log_level = getattr(logging, args.loglevel)
            msg_level = getattr(logging, msg.split(':')[0], -1)

            # print('+'+msg + f" <{msg_level}-{log_level}>")

            if msg_level < log_level:
                continue

            if msg.startswith('CRITICAL'):
                print(Back.RED + msg)
            elif msg.startswith('ERROR'):
                print(Fore.RED + msg)
            elif msg.startswith('WARNING'):
                print(Fore.YELLOW + msg)
            elif msg.startswith('INFO'):
                print(Fore.GREEN + msg)
            elif msg.startswith('DEBUG'):
                print(Fore.BLUE + msg)
            else:
                print(msg)


# ----------------------------------------------------------------------
def main():
    """"""
    asyncio.run(run())


if __name__ == '__main__':
    main()
