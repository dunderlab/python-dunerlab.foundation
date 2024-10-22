"""
This module provides functionalities for managing worker services within a Docker swarm environment.

The `Workers` class offers methods to start, stop, and manage various types of worker services, including Django, Brython, and Python applications. It facilitates the generation of unique worker names, manages port allocations, and controls services efficiently in a containerized setup.

Key functionalities include:
- Managing Docker services for Django, Brython, and Python workers.
- Generating unique names for workers and retrieving available ports.
- Starting and stopping services within a Docker swarm.
"""

import os
import random
import socket
import logging

from string import digits, ascii_letters
import docker
from foundation.utils.swarm import Swarm
from foundation.workers import select_worker

WORKER_NAME = "{}-worker"


########################################################################
class Workers:
    """
    A class to manage worker services within a Docker swarm.

    This class provides methods for starting, stopping, and managing various
    types of worker services (Django, Brython, and Python) within a Docker
    swarm environment. It handles the generation of unique worker names, port
    management, and service control, ensuring efficient operation of worker
    applications.

    Attributes
    ----------
    swarm : Swarm
        An instance of the Swarm class used to manage Docker services.

    Methods
    -------
    gen_worker_name(length: int = 8) -> str
        Generate a unique worker name for services.

    get_open_port() -> int
        Retrieve an available port for service binding.

    stop_all_workers() -> None
        Stop all worker services in the Docker swarm.

    start_django_worker(worker_path: str, service_name: str = None, port: int = None,
                        restart: bool = False, image: str = 'djangoship',
                        tag: str = None, endpoint: str = '', env: dict = {},
                        mounts: list = None, request_ports: dict = {}) -> int
        Start a Django worker service in the Docker swarm.

    start_brython_worker(worker_path: str, service_name: str = None, port: int = None,
                         run: str = "main.py", restart: bool = False, tag: str = '1.1',
                         env: dict = {}, mounts: list = None, request_ports: dict = {}) -> int
        Start a Brython worker service in the Docker swarm.

    start_python_worker(worker_path: str, service_name: str = None, port: int = None,
                        run: str = "main.py", restart: bool = False, tag: str = '1.1',
                        env: dict = {}, mounts: list = None, request_ports: dict = {}) -> int
        Start a Python worker service in the Docker swarm.

    start_worker(worker_path: str, **kwargs: dict) -> None
        Start a worker service in the Docker swarm based on the worker path provided.
    """

    # ----------------------------------------------------------------------
    def __init__(
        self, swarm: Swarm = None, swarm_advertise_addr: str = None
    ):
        """Initialize the Workers class.

        Parameters
        ----------
        swarm : Swarm, optional
            An instance of the Swarm class used to manage Docker services. If not provided,
            a new Swarm instance will be initialized.
        swarm_advertise_addr : str, optional
            The address that the swarm manager advertises to other nodes. If not provided,
            defaults to an internal address for the Docker host.

        Notes
        -----
        This constructor checks if a swarm is already running and initializes it if it is not.
        It ensures that the instance can manage Docker services effectively.
        """

        if (swarm_advertise_addr) and (swarm is None):
            self.swarm = Swarm(advertise_addr=swarm_advertise_addr)
        elif (swarm_advertise_addr is None) and (swarm):
            self.swarm = swarm
        else:
            self.swarm = Swarm()

    # ----------------------------------------------------------------------
    def gen_worker_name(self, length: int = 8) -> str:
        """Generate a unique worker name.

        This method generates a random worker name composed of alphanumeric characters. The name
        format follows the defined pattern `"{worker_name}-worker"` where `worker_name` is a
        string of random characters of specified length.

        Parameters
        ----------
        length : int, optional
            The length of the random string to generate. Defaults to 8.

        Returns
        -------
        str
            A unique worker name that is not currently in use within the swarm services.

        Raises
        ------
        RecursionError
            If a unique worker name cannot be generated after multiple attempts.

        Notes
        -----
        The function ensures that each generated worker name does not already exist in the swarm
        services. If a name collision occurs, it will recursively attempt to generate a new name
        until a unique one is found, which may lead to a `RecursionError` if there are too many
        existing services.
        """
        id_ = "".join(
            [random.choice(ascii_letters + digits) for _ in range(length)]
        )
        if not WORKER_NAME.format(id_) in self.swarm.services:
            return WORKER_NAME.format(id_)
        return self.gen_worker_name(length)

    # ----------------------------------------------------------------------
    def get_open_port(self) -> int:
        """Retrieve an open port for service binding.

        This method creates a socket, binds it to an open port on the host,
        and then returns that port number. This is useful for dynamically
        assigning ports without the risk of collisions with existing services.

        Returns
        -------
        int
            An available port number determined by the operating system.

        Notes
        -----
        The port retrieval is done using a socket in a temporary bind operation,
        which ensures that the port is available at the time of the request.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    # ----------------------------------------------------------------------
    def stop_all_workers(self) -> None:
        """Stop all worker services in the Docker swarm.

        This method iterates through all services registered within the swarm,
        specifically targeting those that are designated as worker services based
        on their naming convention. It invokes the `stop_service` method to
        halt each identified worker service, effectively freeing up resources
        within the Docker environment.

        Raises
        ------
        docker.errors.NotFound
            If any of the services do not exist when attempting to stop them.
        docker.errors.APIError
            If there is an error while attempting to stop the services.

        Notes
        -----
        This method is particularly useful for conducting maintenance or
        deploying new versions of worker services without needing to manually
        stop each service individually.
        """
        for worker in self.swarm.services:
            if worker.endswith(WORKER_NAME.format("")):
                self.swarm.stop_service(worker)

    # ----------------------------------------------------------------------
    def start_django_worker(
        self,
        worker_path: str,
        service_name: str = None,
        port: int = None,
        restart: bool = False,
        image: str = 'djangoship',
        tag: str = None,
        endpoint: str = '',
        env: dict = {},
        mounts: list = None,
        request_ports: dict = {},
    ):
        """Start a Django worker service in the Docker swarm.

        This method initializes and starts a Django worker service within the Docker swarm,
        allowing the execution of a Django application in a containerized environment.

        Parameters
        ----------
        worker_path : str
            The file system path to the worker application. This path can either be absolute
            or relative, and should contain the necessary Django application structure.

        service_name : str, optional
            The name of the service that will be created in the swarm. If not provided, a
            unique worker name will be generated.

        port : int, optional
            The port number on which the Django application will be exposed. If not specified,
            an available port will be dynamically allocated.

        restart : bool, optional
            Indicates whether to restart the service if it already exists. Defaults to False.

        image : str, optional
            The Docker image to use for the Django worker. Defaults to 'djangoship'.

        tag : str, optional
            The tag of the Docker image to be used. If not specified, the default tags ('1.4' for
            'djangoship' and '1.1' for 'djangorun') will be applied.

        endpoint : str, optional
            The endpoint configuration for the service. Defaults to an empty string.

        env : dict, optional
            A dictionary of environment variables to set for the service. Defaults to an empty dictionary.

        mounts : list, optional
            A list of mount points where data can be persisted or shared between the host and container.
            Should be specified as a list of tuples (source, target).

        request_ports : dict, optional
            A dictionary of ports required by the service where the keys are environment variable names
            and the values are the respective port numbers. If a value is None, an open port will be
            automatically assigned.

        Returns
        -------
        int
            The port number on which the Django application is exposed.

        Raises
        ------
        FileNotFoundError
            If the specified worker path does not exist or cannot be accessed.

        docker.errors.NotFound
            If the service could not be found when attempting to restart.

        docker.errors.APIError
            If there is an error creating the service in Docker.

        Notes
        -----
        This method checks if the provided path is valid, generates a service name if not specified,
        handles dynamic port allocation, and manages service creation while ensuring that services
        are stopped and restarted as necessary.
        """
        if tag == None and image == 'djangoship':
            tag = '1.4'
        if tag == None and image == 'djangorun':
            tag = '1.1'

        if os.path.isabs(worker_path) or os.path.exists(worker_path):
            worker_path = os.path.abspath(worker_path)
            app_name = os.path.split(worker_path)[-1]
        elif os.path.exists(select_worker(worker_path)):
            app_name = worker_path
            service_name = WORKER_NAME.format(worker_path.replace("_", "-"))
            worker_path = select_worker(worker_path)
        else:
            logging.warning(f"Service {worker_path} doesn't exits.")
            return

        if port is None:
            port = self.get_open_port()

        if service_name is None:
            service_name = self.gen_worker_name()
        else:
            service_name = WORKER_NAME.format(service_name)
        service_name_env = os.path.split(worker_path)[-1]

        if restart and (service_name in self.swarm.services):
            self.swarm.stop_service(service_name)
            logging.warning(f"Restarting service '{service_name}'")
        elif service_name in self.swarm.services:
            logging.warning(f"Service '{service_name}' already exist")
            return

        endpoint_spec_ports = []
        env_ports = {}
        for port_env in request_ports:
            port_ = request_ports[port_env]
            if port_ is None:
                port_ = self.get_open_port()
            endpoint_spec_ports.append(
                {
                    'Protocol': 'tcp',
                    'PublishedPort': port_,
                    'TargetPort': port_,
                }
            )
            env_ports[port_env] = port_

        docker_mounts = []
        if mounts:
            for source, target in mounts:

                docker_mounts.append(
                    docker.types.Mount(
                        type='bind', source=source, target=target
                    )
                )

        service = self.swarm.client.services.create(
            image=f"dunderlab/{image}:{tag}",
            name=service_name,
            networks=self.swarm.networks,
            hosts=self.swarm.extra_host(),
            endpoint_spec={
                'Ports': [
                    {
                        'Protocol': 'tcp',
                        'PublishedPort': port,
                        'TargetPort': 80,
                    },
                    *endpoint_spec_ports,
                ]
            },
            mounts=[
                docker.types.Mount(
                    type="bind",
                    source=worker_path,
                    target=f"/app/{image}",
                    read_only=False,
                ),
                docker.types.Mount(
                    type="bind",
                    source="/var/run/docker.sock",
                    target="/var/run/docker.sock",
                ),
                *docker_mounts,
            ],
            env={
                "DJANGOPROJECT": app_name,
                "PORT": port,
                "ENDPOINT": endpoint,
                "SERVICE_NAME": service_name_env,
                "WORKER_NAME": service_name,
                **env_ports,
                **env,
            },
        )

        return port

    # ----------------------------------------------------------------------
    def start_brython_worker(
        self,
        worker_path: str,
        service_name: str = None,
        port: int = None,
        run: str = "main.py",
        restart: bool = False,
        tag: str = '1.1',
        env: dict = {},
        mounts: list = None,
        request_ports: dict = {},
        requirements='',
    ):
        """Start a Brython worker service in the Docker swarm.

        This method initializes and starts a Brython worker service within the Docker swarm,
        allowing the execution of a Brython application in a containerized environment.

        Parameters
        ----------
        worker_path : str
            The file system path to the worker application. This path can either be absolute
            or relative, and should contain the necessary Brython application structure.

        service_name : str, optional
            The name of the service that will be created in the swarm. If not provided, a
            unique worker name will be generated.

        port : int, optional
            The port number on which the Brython application will be exposed. If not specified,
            an available port will be dynamically allocated.

        run : str, optional
            The file in the worker application that will be executed. Defaults to "main.py".

        restart : bool, optional
            Indicates whether to restart the service if it already exists. Defaults to False.

        tag : str, optional
            The tag of the Docker image to be used. Defaults to '1.1'.

        env : dict, optional
            A dictionary of environment variables to set for the service. Defaults to an empty dictionary.

        mounts : list, optional
            A list of mount points where data can be persisted or shared between the host and container.
            Should be specified as a list of tuples (source, target).

        request_ports : dict, optional
            A dictionary of ports required by the service where the keys are environment variable names
            and the values are the respective port numbers. If a value is None, an open port will be
            automatically assigned.

        Returns
        -------
        int
            The port number on which the Brython application is exposed.

        Raises
        ------
        FileNotFoundError
            If the specified worker path does not exist or cannot be accessed.

        docker.errors.NotFound
            If the service could not be found when attempting to restart.

        docker.errors.APIError
            If there is an error creating the service in Docker.

        Notes
        -----
        This method checks if the provided path is valid, generates a service name if not specified,
        handles dynamic port allocation, and manages service creation while ensuring that services
        are stopped and restarted as necessary.
        """
        if os.path.isabs(worker_path) or os.path.exists(worker_path):
            worker_path = os.path.abspath(worker_path)
        elif os.path.exists(select_worker(worker_path)):
            service_name = WORKER_NAME.format(worker_path.replace("_", "-"))
            worker_path = select_worker(worker_path)

        if port is None:
            port = self.get_open_port()

        if service_name is None:
            service_name = self.gen_worker_name()
        else:
            service_name = WORKER_NAME.format(service_name)
        service_name_env = os.path.split(worker_path)[-1]

        if restart and (service_name in self.swarm.services):
            self.swarm.stop_service(service_name)
            logging.warning(f"Restarting service '{service_name}'")
        elif service_name in self.swarm.services:
            logging.warning(f"Service '{service_name}' already exist")
            return

        endpoint_spec_ports = []
        env_ports = {}
        for port_env in request_ports:
            port_ = request_ports[port_env]
            if port_ is None:
                port_ = self.get_open_port()
            endpoint_spec_ports.append(
                {
                    'Protocol': 'tcp',
                    'PublishedPort': port_,
                    'TargetPort': port_,
                }
            )
            env_ports[port_env] = port_

        docker_mounts = []
        if mounts:
            for source, target in mounts:

                docker_mounts.append(
                    docker.types.Mount(
                        type='bind', source=source, target=target
                    )
                )

        if requirements:
            requirements = f"pip install --root-user-action=ignore {' '.join(requirements)}"
        else:
            requirements = 'echo'

        service = self.swarm.client.services.create(
            image=f"dunderlab/python312:{tag}",
            name=service_name,
            networks=self.swarm.networks,
            hosts=self.swarm.extra_host(),
            command=[
                "/bin/bash",
                "-c",
                f"ntpd -g && {requirements} && if [ -f \"/app/worker/requirements.txt\" ]; then pip install --root-user-action=ignore -r /app/worker/requirements.txt; fi && if [ -f \"/app/worker/startup.sh\" ]; then /app/worker/startup.sh; fi && python /app/worker/{run}",
            ],
            endpoint_spec={
                'Ports': [
                    {
                        'Protocol': 'tcp',
                        'PublishedPort': port,
                        'TargetPort': port,
                    },
                    *endpoint_spec_ports,
                ]
            },
            mounts=[
                docker.types.Mount(
                    type="bind",
                    source=worker_path,
                    target="/app/worker",
                    read_only=False,
                ),
                docker.types.Mount(
                    type="bind",
                    source="/var/run/docker.sock",
                    target="/var/run/docker.sock",
                ),
                *docker_mounts,
            ],
            env={
                # "STREAM": port_stream,
                "RADIANT": port,
                "PORT": port,
                "SERVICE_NAME": service_name_env,
                "WORKER_NAME": service_name,
                **env_ports,
                **env,
            },
        )

        return port

    # ----------------------------------------------------------------------
    def start_python_worker(
        self,
        worker_path: str,
        service_name: str = None,
        port: int = None,
        run: str = "main.py",
        restart: bool = False,
        tag: str = '1.1',
        env: dict = {},
        mounts: list = None,
        request_ports: dict = {},
        requirements='',
    ):
        """Start a Python worker service in the Docker swarm.

        This method initializes and starts a Python worker service within the Docker swarm,
        allowing the execution of a Python application in a containerized environment.

        Parameters
        ----------
        worker_path : str
            The file system path to the worker application. This path can either be absolute
            or relative and should contain the necessary Python application structure.

        service_name : str, optional
            The name of the service that will be created in the swarm. If not provided, a
            unique worker name will be generated.

        port : int, optional
            The port number on which the Python application will be exposed. If not specified,
            an available port will be dynamically allocated.

        run : str, optional
            The file in the worker application that will be executed. Defaults to "main.py".

        restart : bool, optional
            Indicates whether to restart the service if it already exists. Defaults to False.

        tag : str, optional
            The tag of the Docker image to be used. Defaults to '1.1'.

        env : dict, optional
            A dictionary of environment variables to set for the service. Defaults to an empty dictionary.

        mounts : list, optional
            A list of mount points where data can be persisted or shared between the host and container.
            Should be specified as a list of tuples (source, target).

        request_ports : dict, optional
            A dictionary of ports required by the service where the keys are environment variable names
            and the values are the respective port numbers. If a value is None, an open port will be
            automatically assigned.

        Returns
        -------
        int
            The port number on which the Python application is exposed.

        Raises
        ------
        FileNotFoundError
            If the specified worker path does not exist or cannot be accessed.

        docker.errors.NotFound
            If the service could not be found when attempting to restart.

        docker.errors.APIError
            If there is an error creating the service in Docker.

        Notes
        -----
        This method checks if the provided path is valid, generates a service name if not specified,
        handles dynamic port allocation, and manages service creation while ensuring that services
        are stopped and restarted as necessary.
        """
        if os.path.isabs(worker_path) or os.path.exists(worker_path):
            worker_path = os.path.abspath(worker_path)
        elif os.path.exists(select_worker(worker_path)):
            service_name = WORKER_NAME.format(worker_path.replace("_", "-"))
            worker_path = select_worker(worker_path)

        if port is None:
            port = self.get_open_port()

        if service_name is None:
            service_name = self.gen_worker_name()
        else:
            service_name = WORKER_NAME.format(service_name)
        service_name_env = os.path.split(worker_path)[-1]

        if restart and (service_name in self.swarm.services):
            self.swarm.stop_service(service_name)
            logging.warning(f"Restarting service '{service_name}'")
        elif service_name in self.swarm.services:
            logging.warning(f"Service '{service_name}' already exist")
            return

        endpoint_spec_ports = []
        env_ports = {}
        for port_env in request_ports:
            port_ = request_ports[port_env]
            if port_ is None:
                port_ = self.get_open_port()
            endpoint_spec_ports.append(
                {
                    'Protocol': 'tcp',
                    'PublishedPort': port_,
                    'TargetPort': port_,
                }
            )
            env_ports[port_env] = port_

        docker_mounts = []
        if mounts:
            for source, target in mounts:

                docker_mounts.append(
                    docker.types.Mount(
                        type='bind', source=source, target=target
                    )
                )

        if requirements:
            requirements = f"pip install --root-user-action=ignore {' '.join(requirements)}"
        else:
            requirements = 'echo'

        service = self.swarm.client.services.create(
            image=f"dunderlab/python312:{tag}",
            name=service_name,
            networks=self.swarm.networks,
            hosts=self.swarm.extra_host(),
            command=[
                "/bin/bash",
                "-c",
                f"ntpd -g && {requirements} && if [ -f \"/app/worker/requirements.txt\" ]; then pip install --root-user-action=ignore -r /app/worker/requirements.txt; fi && if [ -f \"/app/worker/startup.sh\" ]; then /app/worker/startup.sh; fi && python /app/worker/{run}",
            ],
            endpoint_spec={
                'Ports': [
                    {
                        'Protocol': 'tcp',
                        'PublishedPort': port,
                        'TargetPort': port,
                    },
                    *endpoint_spec_ports,
                ]
            },
            mounts=[
                docker.types.Mount(
                    type="bind",
                    source=worker_path,
                    target="/app/worker",
                    read_only=False,
                ),
                docker.types.Mount(
                    type="bind",
                    source="/var/run/docker.sock",
                    target="/var/run/docker.sock",
                ),
                *docker_mounts,
            ],
            env={
                "PORT": port,
                "SERVICE_NAME": service_name_env,
                "WORKER_NAME": service_name,
                **env_ports,
                **env,
            },
        )

        return port

    # ----------------------------------------------------------------------
    def start_worker(self, worker_path: str, **kwargs: dict) -> None:
        """Start a worker service in the Docker swarm.

        This method initializes and starts a worker service based on the
        provided worker path. It detects the type of worker (Django, Brython,
        or Python) and delegates the starting of the service to the corresponding
        method.

        Parameters
        ----------
        worker_path : str
            The file system path to the worker application. This path can be either
            absolute or relative, and it should contain the necessary worker application
            structure.

        kwargs : dict
            Additional keyword arguments that may be required by the specific worker
            service being started (e.g., `service_name`, `port`, etc.).

        Returns
        -------
        None
            The function does not return a value.

        Raises
        ------
        FileNotFoundError
            If the specified worker path does not exist or cannot be accessed.

        Notes
        -----
        - This method relies on the presence of specific files (e.g., `manage.py` for
          Django or `main.py` for Brython and Python) in the provided worker path to
          identify the type of service to be started.
        - The method also ensures that the service name is formatted appropriately
          before starting the worker.
        """
        if os.path.isabs(worker_path) or os.path.exists(worker_path):
            worker_path = os.path.abspath(worker_path)
        elif os.path.exists(select_worker(worker_path)):
            if not 'service_name' in kwargs:
                kwargs['service_name'] = worker_path
            worker_path = select_worker(worker_path)
            kwargs['service_name'] = kwargs['service_name'].replace('_', '-')

        if os.path.exists(os.path.join(worker_path, 'manage.py')):
            logging.warning('Running a Django worker')
            return self.start_django_worker(worker_path, **kwargs)  # Django
        elif os.path.exists(os.path.join(worker_path, 'main.py')):
            with open(os.path.join(worker_path, 'main.py'), 'r') as file:
                content = file.read()
                if 'from foundation.radiant.server' in content:
                    logging.warning('Running a Brython worker')
                    return self.start_brython_worker(
                        worker_path, **kwargs
                    )  # Brython
                else:
                    logging.warning('Running a Pyhton worker')
                    return self.start_python_worker(
                        worker_path, **kwargs
                    )  # Python
        else:
            logging.warning('Impossible to detect a Worker')
