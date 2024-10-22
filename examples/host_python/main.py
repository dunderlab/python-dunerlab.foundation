import time
from datetime import datetime
import logging
import os


with open(
    '/home/yeison/Development/PythonDev/DunderLab/python-dunderlab.foundation/examples/host_python/logs.txt',
    'a',
) as logfile:
    logfile.write(f'START\n')

while True:
    time.sleep(1)

    logging.warning(f'Loop {datetime.now()}')
    with open(
        '/home/yeison/Development/PythonDev/DunderLab/python-dunderlab.foundation/examples/host_python/logs.txt',
        'a',
    ) as logfile:
        logfile.write(f'Loop {datetime.now()}\n')
