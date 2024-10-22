from foundation.utils.host_workers import HostWorker


host_worker = HostWorker()


host_worker.start_worker('host_python', service_name='1')
host_worker.start_worker('host_python', service_name='12')

host_worker
