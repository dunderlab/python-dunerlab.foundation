#!/usr/bin/env python

import os
import argparse
from foundation.utils import Workers
from foundation.utils.workers import WORKER_NAME

parser = argparse.ArgumentParser(description="Start an HCI worker.")
parser.add_argument(
    '-w', '--worker', default='.', help="Path of the worker's directory."
)
parser.add_argument(
    '-s', '--service_name', default=None, help="Name of the service."
)
parser.add_argument(
    '-r',
    '--restart',
    action='store_true',
    default=True,
    help="Option to restart the worker.",
)
parser.add_argument(
    '-k',
    '--kill',
    action='store_true',
    default=False,
    help="Option to kill the worker.",
)

args = parser.parse_args()

workers = Workers()


# ----------------------------------------------------------------------
def main():
    """"""

    if args.kill:
        workers.swarm.stop_service(WORKER_NAME.format(args.service_name))
    else:
        w = os.curdir if args.worker == '.' else args.worker
        workers.start_worker(
            w, service_name=args.service_name, restart=args.restart
        )


if __name__ == '__main__':
    main()
