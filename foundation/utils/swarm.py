"""
This module defines the Swarm class, which provides an interface for managing
a Docker Swarm environment. It includes functionalities for creating and managing
services, networks, volumes, and retrieving operation statistics within the swarm.

Key functionalities include:
- Initializing a Docker Swarm.
- Creating and deleting Docker volumes.
- Managing services and networking in the Swarm.
- Retrieving runtime statistics for services.
- Starting various services like NTP, JupyterLab, Kafka, and TimescaleDB.

"""

import docker
import logging
import netifaces


########################################################################
class Swarm:
    """A class to manage a Docker Swarm environment.

    This class provides functionality for initializing and managing
    a Docker Swarm, including creating and managing services,
    networks, volumes, and retrieving statistics.

    Attributes
    ----------
    client : docker.DockerClient
        A Docker client instance used to communicate with the Docker daemon.
    networks : list
        A list of network names available in the swarm.

    Methods
    -------
    create_networks() -> None
        Creates necessary overlay networks for the swarm services.

    create_volume(volume_name: str) -> str
        Creates a new Docker volume if it does not already exist.

    delete_volume(volume_name: str) -> None
        Deletes an existing Docker volume from the swarm.

    services() -> list
        Retrieves a list of active service names in the swarm.

    containers(attr: str = 'id') -> list
        Retrieves a list of container IDs currently running in the swarm.

    volumes() -> list
        Retrieves a list of Docker volumes currently active in the swarm.

    stop_service(service_name: str) -> None
        Stops a specified service in the swarm by name.

    restart_service(service_name: str) -> None
        Restarts a specified service in the swarm.

    stop_all_services() -> list
        Stops all running services in the swarm at once.

    stats(service_name: str) -> list
        Retrieves runtime statistics for a specified service.

    start_ntp(service_name: str = "ntp-service", port: int = 123,
              restart: bool = False, tag: str = '1.0') -> bool
        Starts an NTP service in the Docker swarm.

    start_jupyterlab(service_name: str = "jupyterlab-service", port: int = 8888,
                     restart: bool = False, tag: str = '1.1',
                     volume_name: str = None, mounts: list = None,
                     env: dict = {}) -> bool
        Starts a JupyterLab service in the Docker swarm.

    start_kafka(kafka_service_name: str = "kafka-service",
                 zookeeper_service_name: str = "zookeeper-service",
                 kafka_port: int = 9092, kafka_port_external: int = 19092,
                 zookeeper_port: int = 2181, restart: bool = False,
                 tag: str = '1.1') -> tuple
        Starts Kafka and Zookeeper services in the Docker swarm.

    start_timescaledb(service_name: str = "timescaledb-service",
                       port: int = 5432, volume_name: str = None,
                       restart: bool = False, tag: str = 'latest-pg15') -> bool
        Starts a TimescaleDB service in the Docker swarm.
    """

    # ----------------------------------------------------------------------
    def __init__(
        self,
        base_url: str = 'unix://var/run/docker.sock',
        advertise_addr: str = '',
    ):
        """Initialize the Swarm class instance.

        Parameters
        ----------
        base_url : str, optional
            The URL for the Docker base socket, by default 'unix://var/run/docker.sock'.
        advertise_addr : str, optional
            The address which the swarm manager advertises to other nodes, by default ''.

        Raises
        ------
        docker.errors.APIError
            If there is an error communicating with the Docker daemon.

        Notes
        -----
        This constructor checks if a swarm is already running and initializes it
        if it is not. It also creates the default overlay networks required for the services.
        """
        self.client = docker.DockerClient(base_url=base_url)
        try:
            logging.warning("Starting swarm...")
            if not self.client.swarm.attrs.get('ID'):
                swarm_init_response = self.client.swarm.init(
                    advertise_addr=advertise_addr
                )
                logging.warning(f"Swarm started, ID: {swarm_init_response}")
            else:
                logging.warning(
                    f"Swarm is already running, ID: {self.client.swarm.attrs.get('ID')}"
                )
        except docker.errors.APIError as e:
            logging.warning("Error:", str(e))
            return

        self.create_networks()

    # ----------------------------------------------------------------------
    def create_networks(self) -> None:
        """Create overlay networks for the swarm services.

        This method checks if predefined networks exist in the swarm.
        If a network does not exist, it creates a new overlay network.

        Notes
        -----
        Currently, the following networks are created:
        - foundation_network
        """
        self.networks = ['foundation_network']
        logging.warning("Creating networks...")
        for network in self.networks:
            if network not in [n.name for n in self.client.networks.list()]:
                self.client.networks.create(network, driver="overlay")
                logging.warning(f"Created network '{network}'")

    # ----------------------------------------------------------------------
    def create_volume(self, volume_name: str) -> str:
        """Create a Docker volume.

        This method creates a new volume in the Docker swarm if it does not
        already exist. Volumes are used for persisting data shared among
        containers.

        Parameters
        ----------
        volume_name : str
            The name of the volume to create.
            If the name does not end with '-volume', it will be appended.

        Returns
        -------
        str
            The name of the created volume.

        Raises
        ------
        docker.errors.APIError
            If there is an error while creating the volume.

        Notes
        -----
        This method ensures that the volume name complies with Docker
        naming conventions and handles any potential errors that may arise
        during the volume creation process.
        """
        logging.warning("Creating volumes...")
        if not volume_name in self.volumes:
            if not volume_name.endswith('-volume'):
                volume_name = f'{volume_name}-volume'
            self.client.volumes.create(name=volume_name)
        else:
            logging.warning(f"Volume '{volume_name}' already exists")

        return volume_name

    # ----------------------------------------------------------------------
    def delete_volume(self, volume_name: str) -> None:
        """Delete a Docker volume.

        This method removes an existing volume from the Docker swarm. If the
        volume does not exist, a warning is logged.

        Parameters
        ----------
        volume_name : str
            The name of the volume to delete. The name must comply with Docker
            naming conventions.

        Raises
        ------
        docker.errors.NotFound
            If the volume does not exist.
        docker.errors.APIError
            If there is an error while attempting to remove the volume.

        Notes
        -----
        Ensure that the volume is not being used by any containers before attempting
        to delete it.
        """
        logging.warning("Deleting volumes...")
        try:
            volume = self.client.volumes.get(volume_name)
            volume.remove()
            logging.info(f"Volume '{volume_name}' has been deleted.")
        except docker.errors.NotFound:
            logging.warning(f"Volume '{volume_name}' does not exist.")
        except docker.errors.APIError as e:
            logging.error(
                f"An error occurred while attempting to remove the volume: {e}"
            )

        return None

    # ----------------------------------------------------------------------
    @property
    def services(self, attr='name') -> list:
        """Retrieve a list of service names in the swarm.

        This property fetches the current services running in the swarm and
        returns their names. The names can be used to identify and manage
        specific services within the swarm.

        Returns
        -------
        list
            A list of service names currently active in the swarm.

        Examples
        --------
        >>> swarm = Swarm()
        >>> services = swarm.services
        >>> print(services)
        ['service_name_1', 'service_name_2', ...]
        """
        return [
            getattr(service, attr) for service in self.client.services.list()
        ]

    # ----------------------------------------------------------------------
    @property
    def containers(self, attr: str = 'id') -> list:
        """Retrieve a list of container IDs in the swarm.

        This property retrieves the currently running containers in the
        Docker swarm and returns their IDs.

        Parameters
        ----------
        attr : str, optional
            The attribute to retrieve from the container objects. By default,
            the container ID is retrieved.

        Returns
        -------
        list
            A list of container IDs currently active in the swarm.
        """
        return [
            getattr(container, attr)
            for container in self.client.containers.list()
        ]

    # ----------------------------------------------------------------------
    @property
    def volumes(self) -> list:
        """Retrieve a list of Docker volumes in the swarm.

        This property fetches the currently available volumes in the Docker swarm
        and returns their names. The volume names can be used for managing persistent
        data shared among containers.

        Returns
        -------
        list
            A list of volume names currently active in the swarm that adhere to
            Docker naming conventions (ending with '-volume').
        """
        return [
            v.name
            for v in self.client.volumes.list()
            if v.name.endswith('-volume')
        ]

    # ----------------------------------------------------------------------
    def stop_service(self, service_name: str) -> None:
        """Stop a running service in the Docker swarm.

        This method removes a specified service from the swarm. It ensures
        the service is properly stopped and removed, freeing up resources.

        Parameters
        ----------
        service_name : str
            The name of the service to stop. It must match the name of an
            existing service in the swarm.

        Raises
        ------
        docker.errors.NotFound
            If the service does not exist or has already been removed.
        docker.errors.APIError
            If there is an error while attempting to remove the service.

        Notes
        -----
        Ensure that the service is not being used by any containers that
        could prevent it from stopping.
        """
        service = self.client.services.get(service_name)
        return service.remove()

    # ----------------------------------------------------------------------
    def restart_service(self, service_name: str) -> None:
        """Restart a service in the Docker swarm.

        This method updates and restarts the specified service specified by
        its name, forcing an update to occur even if there are no changes
        to the service.

        Parameters
        ----------
        service_name : str
            The name of the service to restart. It must match the name
            of an existing service in the swarm.

        Raises
        ------
        docker.errors.NotFound
            If the service does not exist or has already been removed.
        docker.errors.APIError
            If there is an error while attempting to update the service.

        Notes
        -----
        Restarting the service can help apply new changes or configurations
        without needing to stop and remove the service entirely.
        """
        service = self.client.services.get(service_name)
        return service.update(force_update=True)

    # ----------------------------------------------------------------------
    def stop_all_services(self) -> list:
        """Stop all running services in the Docker swarm.

        This method iterates through all services in the swarm and
        stops each one. It is a convenient way to halt all services
        at once, freeing up resources used by the containers associated
        with these services.

        Returns
        -------
        list
            A list of service names that were successfully stopped.

        Raises
        ------
        docker.errors.NotFound
            If any of the services do not exist when attempting to stop them.
        docker.errors.APIError
            If there is an error while attempting to stop the services.

        Notes
        -----
        Ensure that stopping services does not affect dependent services
        or processes.
        """
        return [self.stop_service(service) for service in self.services]

    # ----------------------------------------------------------------------
    def stats(self, service_name: str) -> list:
        """Retrieve statistics for a specific service in the Docker swarm.

        This method gathers and returns runtime statistics for the specified
        service. The statistics include information such as CPU usage, memory
        consumption, and network I/O. Useful for monitoring service performance.

        Parameters
        ----------
        service_name : str
            The name of the service for which to retrieve statistics. This name
            must match one of the currently running services in the swarm.

        Returns
        -------
        list
            A list of dictionaries containing statistics for each task of the
            specified service. Each dictionary includes various metrics, which
            can be used for monitoring and debugging purposes.

        Raises
        ------
        docker.errors.NotFound
            If the specified service does not exist in the swarm.
        docker.errors.APIError
            If there is an error while attempting to retrieve stats for the service.

        Notes
        -----
        Ensure that the service is running before attempting to retrieve its
        statistics.
        """
        service = self.client.services.get(service_name)
        stats = []
        for task in service.tasks():
            container_id = task['Status']['ContainerStatus']['ContainerID']
            if container_id in self.containers:
                stats.append(
                    self.client.containers.get(container_id).stats(
                        stream=False
                    )
                )
        return stats

    # ----------------------------------------------------------------------
    def start_ntp(
        self,
        service_name: str = "ntp-service",
        port: int = 123,
        restart: bool = False,
        tag: str = '1.0',
    ):
        """Start an NTP service in the Docker swarm.

        This method creates and starts an NTP service within the Docker swarm,
        allowing for network time synchronization.

        Parameters
        ----------
        service_name : str, optional
            The name of the NTP service to create. Defaults to "ntp-service".
        port : int, optional
            The port to expose for the NTP service. Defaults to 123.
        restart : bool, optional
            If True, the method will attempt to restart the service if it
            already exists. Defaults to False.
        tag : str, optional
            The tag for the Docker image to use. Defaults to '1.0'.

        Returns
        -------
        bool
            True if the service was successfully started, False if it already
            exists or if an error occurred during creation.

        Raises
        ------
        docker.errors.APIError
            If there is an error while attempting to create the service.

        Notes
        -----
        Ensure that port 123 is not already in use on the host machine to
        avoid conflicts during service creation.
        """
        if restart and (service_name in self.services):
            self.stop_service(service_name)
            logging.warning(f"Restarting service '{service_name}'")
        elif service_name in self.services:
            logging.warning(f"Service '{service_name}' already exist")
            return

        service = self.client.services.create(
            image=f'dunderlab/ntp:{tag}',
            name=service_name,
            networks=self.networks,
            endpoint_spec={
                'Ports': [
                    {
                        'Protocol': 'udp',
                        'PublishedPort': port,
                        'TargetPort': 123,
                    },
                ]
            },
            env=[
                f"PORT={port}",
            ],
        )

        return service_name in self.services

    # ----------------------------------------------------------------------
    def start_jupyterlab(
        self,
        service_name: str = "jupyterlab-service",
        port: int = 8888,
        restart: bool = False,
        tag: str = '1.1',
        volume_name: str = None,
        mounts: list = None,
        env: dict = {},
        requirements='',
    ):
        """Start a JupyterLab service in the Docker swarm.

        This method creates and starts a JupyterLab service within the Docker swarm,
        allowing users to access an interactive Jupyter notebook environment.

        Parameters
        ----------
        service_name : str, optional
            The name of the JupyterLab service to create. Defaults to "jupyterlab-service".
        port : int, optional
            The port to expose for the JupyterLab service. Defaults to 8888.
        restart : bool, optional
            If True, the method will attempt to restart the service if it
            already exists. Defaults to False.
        tag : str, optional
            The tag for the Docker image to use. Defaults to '1.1'.
        volume_name : str, optional
            The name of the Docker volume to attach for persisting data.
            If not provided, a new volume will be created.
        mounts : list, optional
            Additional mounts for the service, specified as a list of tuples
            containing source and target paths.
        env : dict, optional
            Environment variables to set for the JupyterLab service.

        Returns
        -------
        bool
            True if the service was successfully started, False if it already
            exists or if an error occurred during creation.

        Raises
        ------
        docker.errors.APIError
            If there is an error while attempting to create the service.

        Notes
        -----
        Ensure that the required ports are not already in use on the host machine to
        avoid conflicts during service creation.
        """
        if restart and (service_name in self.services):
            self.stop_service(service_name)
            logging.warning(f"Restarting service '{service_name}'")
        elif service_name in self.services:
            logging.warning(f"Service '{service_name}' already exist")
            return

        if volume_name is None:
            volume_name = self.create_volume(service_name)
        else:
            volume_name = self.create_volume(volume_name)

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

        service = self.client.services.create(
            image=f"dunderlab/python312:{tag}",
            name=service_name,
            networks=self.networks,
            command=[
                "/bin/bash",
                "-c",
                f"{requirements} && jupyter lab --notebook-dir='/app' --ip=0.0.0.0 --port=8888 --allow-root --NotebookApp.token='' --NotebookApp.password=''",
            ],
            endpoint_spec={
                'Ports': [
                    {
                        'Protocol': 'tcp',
                        'PublishedPort': 8888,
                        'TargetPort': port,
                    },
                ]
            },
            hosts=self.extra_host(),
            mounts=[
                docker.types.Mount(
                    type='bind',
                    source='/var/run/docker.sock',
                    target='/var/run/docker.sock',
                ),
                docker.types.Mount(
                    target='/app',
                    source=volume_name,
                    type="volume",
                    read_only=False,
                ),
                *docker_mounts,
            ],
            env={
                f"PORT": port,
                # "NTP_SERVER=ntp-service",
                **env,
            },
        )
        return service_name in self.services

    # ----------------------------------------------------------------------
    def start_kafka(
        self: "Swarm",
        kafka_service_name: str = "kafka-service",
        zookeeper_service_name: str = "zookeeper-service",
        kafka_port: int = 9092,
        kafka_port_external: int = 19092,
        zookeeper_port: int = 2181,
        restart: bool = False,
        tag: str = '1.1',
    ):
        """Start Kafka and Zookeeper services in the Docker swarm.

        This method initializes and starts both Kafka and Zookeeper services
        within the Docker swarm. It allows for message brokering and
        management of service instances to provide a reliable streaming
        platform.

        Parameters
        ----------
        kafka_service_name : str, optional
            The name of the Kafka service to create. Defaults to "kafka-service".
        zookeeper_service_name : str, optional
            The name of the Zookeeper service to create. Defaults to "zookeeper-service".
        kafka_port : int, optional
            The internal port for Kafka service. Defaults to 9092.
        kafka_port_external : int, optional
            The external port exposed for Kafka service. Defaults to 19092.
        zookeeper_port : int, optional
            The port exposed for Zookeeper service. Defaults to 2181.
        restart : bool, optional
            If True, the method will attempt to restart the services if they
            already exist. Defaults to False.
        tag : str, optional
            The tag for the Docker images to use. Defaults to '1.1'.

        Returns
        -------
        tuple
            A tuple indicating whether the Kafka and Zookeeper services were
            successfully started. The first element corresponds to the Kafka service
            status and the second to the Zookeeper service status.

        Raises
        ------
        docker.errors.APIError
            If there is an error while attempting to create the services.

        Notes
        -----
        Ensure that the specified service names do not conflict with existing
        services in the swarm to avoid unintended behavior.
        """
        if restart and (kafka_service_name in self.services):
            self.stop_service(kafka_service_name)
            logging.warning(f"Restarting service '{kafka_service_name}'")

        if restart and (zookeeper_service_name in self.services):
            self.stop_service(zookeeper_service_name)
            logging.warning(f"Restarting service '{zookeeper_service_name}'")

        if not kafka_service_name in self.services:
            kafka_service = self.client.services.create(
                image=f"dunderlab/kafka:{tag}",
                # restart_policy=docker.types.RestartPolicy(condition='any'),
                name=kafka_service_name,
                networks=self.networks,
                endpoint_spec={
                    'Ports': [
                        {
                            'Protocol': 'tcp',
                            'PublishedPort': kafka_port,
                            'TargetPort': kafka_port,
                        },
                        {
                            'Protocol': 'tcp',
                            'PublishedPort': kafka_port_external,
                            'TargetPort': kafka_port_external,
                        },
                    ]
                },
                env=[
                    f"KAFKA_ZOOKEEPER_CONNECT={zookeeper_service_name}:{zookeeper_port}",
                    f"KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT",
                    f"KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://{kafka_service_name}:{kafka_port},PLAINTEXT_HOST://localhost:{kafka_port_external}",
                    f"PORT={kafka_port_external}",
                ],
            )
        else:
            logging.warning(f"Service '{kafka_service_name}' already exist")

        if not zookeeper_service_name in self.services:
            zookeeper_service = self.client.services.create(
                image=f"dunderlab/zookeeper:{tag}",
                name=zookeeper_service_name,
                networks=self.networks,
                endpoint_spec={
                    'Ports': [
                        {
                            'Protocol': 'tcp',
                            'PublishedPort': zookeeper_port,
                            'TargetPort': zookeeper_port,
                        },
                    ]
                },
                env=[
                    f"ZOOKEEPER_CLIENT_PORT={zookeeper_port}",
                ],
            )
        else:
            logging.warning(
                f"Service '{zookeeper_service_name}' already exist"
            )

        return (
            kafka_service_name in self.services,
            zookeeper_service_name in self.services,
        )

    # ----------------------------------------------------------------------
    def start_kafka_logs(
        self,
        kafka_service_name: str = "kafka-logs-service",
        zookeeper_service_name: str = "zookeeper-logs-service",
        kafka_port: int = 9093,
        kafka_port_external: int = 19093,
        zookeeper_port: int = 2182,
        restart: bool = False,
        tag: str = '1.1',
    ):
        """Start Kafka and Zookeeper logging services in the Docker swarm.

        This method initializes and starts both Kafka and Zookeeper logging services
        within the Docker swarm, providing a mechanism for capturing and managing
        logs generated by Kafka and Zookeeper instances.

        Parameters
        ----------
        kafka_service_name : str, optional
            The name of the Kafka logging service to create. Defaults to "kafka-logs-service".
        zookeeper_service_name : str, optional
            The name of the Zookeeper logging service to create. Defaults to "zookeeper-logs-service".
        kafka_port : int, optional
            The internal port for Kafka logging service. Defaults to 9093.
        kafka_port_external : int, optional
            The external port exposed for Kafka logging service. Defaults to 19093.
        zookeeper_port : int, optional
            The port exposed for Zookeeper logging service. Defaults to 2182.
        restart : bool, optional
            If True, the method will attempt to restart the services if they
            already exist. Defaults to False.
        tag : str, optional
            The tag for the Docker images to use. Defaults to '1.1'.

        Returns
        -------
        tuple
            A tuple indicating whether the Kafka logging and Zookeeper logging services were
            successfully started. The first element corresponds to the Kafka logging service
            status and the second to the Zookeeper logging service status.

        Raises
        ------
        docker.errors.APIError
            If there is an error while attempting to create the services.

        Notes
        -----
        Ensure that the specified service names do not conflict with existing
        services in the swarm to avoid unintended behavior.
        """
        """"""
        return self.start_kafka(
            kafka_service_name,
            zookeeper_service_name,
            kafka_port,
            kafka_port_external,
            zookeeper_port,
            restart,
            tag,
        )

    # ----------------------------------------------------------------------
    def start_timescaledb(
        self,
        service_name: str = "timescaledb-service",
        port: int = 5432,
        volume_name: str = None,
        restart: bool = False,
        tag: str = 'latest-pg15',
    ):
        """Start a TimescaleDB service in the Docker swarm.

        This method initializes and starts a TimescaleDB service within the
        Docker swarm, providing a robust time-series database solution.

        Parameters
        ----------
        service_name : str, optional
            The name of the TimescaleDB service to create.
            Defaults to "timescaledb-service".
        port : int, optional
            The port on which the TimescaleDB service will be exposed.
            Defaults to 5432.
        volume_name : str, optional
            The name of the Docker volume to attach for persisting data.
            If not provided, a new volume will be created.
        restart : bool, optional
            If True, the method will attempt to restart the service if it
            already exists. Defaults to False.
        tag : str, optional
            The tag for the Docker image to use. Defaults to 'latest-pg15'.

        Returns
        -------
        bool
            True if the TimescaleDB service was successfully
            started, False if it already exists or if an error occurred during creation.

        Raises
        ------
        docker.errors.APIError
            If there is an error while attempting to create the service.

        Notes
        -----
        Ensure that the specified service name does not conflict with
        existing services in the swarm to avoid unintended behavior.
        """
        """"""
        if restart and (service_name in self.services):
            self.stop_service(service_name)
            logging.warning(f"Restarting service '{service_name}'")
        elif service_name in self.services:
            logging.warning(f"Service '{service_name}' already exist")
            return

        if volume_name is None:
            volume_name = self.create_volume(service_name)
        else:
            volume_name = self.create_volume(volume_name)

        timescaledb_service = self.client.services.create(
            image=f"timescale/timescaledb:{tag}",
            name=service_name,
            networks=self.networks,
            env=[
                "POSTGRES_PASSWORD=password",
                "POSTGRES_USER=postgres",
                "POSTGRES_DB=timescaledb",
                "POSTGRES_MAX_CONNECTIONS=500",
                f"PORT={port}",
            ],
            endpoint_spec={
                'Ports': [
                    {
                        'Protocol': 'tcp',
                        'PublishedPort': 5432,
                        'TargetPort': port,
                    },
                ]
            },
            mounts=[
                docker.types.Mount(
                    target='/var/lib/postgresql/data',
                    source=volume_name,
                    type="volume",
                    read_only=False,
                ),
            ],
        )
        return service_name in self.services

    # ----------------------------------------------------------------------
    def get_join_command(self) -> str:
        """Retrieve the command to join the swarm as a worker node.

        This method constructs and returns a Docker command that allows
        a worker node to join the existing swarm managed by the current
        node. The command contains the necessary token and address
        required for the worker to successfully join.

        Returns
        -------
        str
            A formatted string that represents the Docker command for
            joining the swarm as a worker. The command includes the worker
            join token and manager address.

        Notes
        -----
        This method will only work if the current node is part of an
        active swarm and has control available. If the swarm is not
        initialized or if control is not available, this method may
        return None or result in an error.
        """
        swarm_info = self.client.info().get('Swarm')
        if swarm_info and swarm_info.get('ControlAvailable'):
            worker_join_token = self.client.swarm.attrs['JoinTokens'][
                'Worker'
            ]
            manager_addr = swarm_info.get('RemoteManagers')[0].get('Addr')
            return f'docker swarm join --token {worker_join_token} {manager_addr}'

    # ----------------------------------------------------------------------
    def advertise_addr(self) -> str:
        """Retrieve the address of the swarm manager.

        This method checks the current swarm information and returns the
        address of the manager node. This address can be used by worker
        nodes to join the swarm or for communication purposes.

        Returns
        -------
        str
            The address of the swarm manager, formatted as a string.
            Returns None if the swarm is not initialized or if control
            is not available.

        Notes
        -----
        This method ensures that it only fetches the address if the
        current node is part of an active swarm that has control available.
        """
        swarm_info = self.client.info().get('Swarm')
        if swarm_info and swarm_info.get('ControlAvailable'):
            manager_addr = swarm_info.get('RemoteManagers')[0].get('Addr')
            return manager_addr

    # ----------------------------------------------------------------------
    def extra_host(self) -> dict:
        """Retrieve the addresses of network interfaces for Docker.

        This method checks all available network interfaces on the host machine
        and returns a dictionary mapping the interface names to their corresponding
        IPv4 addresses. This information can be useful for configuring services
        that need to bind to specific network interfaces or for identifying
        available network resources.

        Returns
        -------
        dict
            A dictionary where each key is a formatted string representing
            the host alias for the Docker container (e.g., 'host.docker.<interface>'),
            and each value is the corresponding IPv4 address for that interface.

        Notes
        -----
        The retrieved addresses can be utilized to manage service networking
        within a Docker Swarm setup. Only interfaces with valid IPv4 addresses
        are included in the returned dictionary.
        """
        interfaces = netifaces.interfaces()
        ips = {}

        for interface in interfaces:
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                ip_info = addrs[netifaces.AF_INET][0]
                ips[interface] = ip_info['addr']

        return {
            f"host.docker.{interface}": ips[interface] for interface in ips
        }
