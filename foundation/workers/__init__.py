import os

workers_location = os.path.dirname(__file__)


# ----------------------------------------------------------------------
def select_worker(worker):
    """"""
    return os.path.join(workers_location, worker)


# ----------------------------------------------------------------------
def list_workers():
    """"""
    workers = []
    for item in os.listdir(workers_location):
        if os.path.isdir(os.path.join(workers_location, item)) and not item.startswith('__'):
            workers.append(item)
    return workers



########################################################################
class LazyWorkers:
    """"""

    # ----------------------------------------------------------------------
    def __init__(self, workers):
        """"""
        self.workers = workers


    # ----------------------------------------------------------------------
    def start_timescaledb_api(self, port=51102, restart=False):
        """"""
        return self.workers.start_worker(
            'timescaledb_api',
            service_name='timescaledb_api',
            image='djangorun',
            endpoint='/timescaledbapp/',
            port=port,
            restart=restart,
        )
