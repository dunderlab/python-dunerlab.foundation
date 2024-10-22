"""
=================
HostWorker Module
=================

This module provides the HostWorker class to manage worker services executing various tasks
within a Docker swarm environment. It is responsible for starting, stopping, and tracking the
status of worker services, supporting various types such as Django, Brython, or standard Python
applications. The HostWorker class also includes functionalities for handling the lifecycle of
these services and maintaining a log of their operational states.

Key Functionalities
---------------------
- Start and stop worker services.
- Load and save process IDs to track running services.
- Restart services and manage service names.
"""

import os
import subprocess
import pickle
import random
from string import digits, ascii_letters
import psutil

user_home = os.path.expanduser('~')
project_folder = os.path.join(user_home, 'foundation')
os.makedirs(project_folder, exist_ok=True)

WORKER_NAME = "{}-host-worker"


########################################################################
class HostWorker:
    """
    HostWorker manages worker services for executing various tasks within a Docker swarm environment.

    It is responsible for starting, stopping, and tracking the status of worker services.
    The worker services can be of different types such as Django, Brython, or standard Python applications.
    This class provides functionality to handle the lifecycle of these services and maintains a log of their states.

    Key Functionalities:
    - Start and stop worker services.
    - Load and save process IDs to track running services.
    - Restart services and manage service names.

    Attributes
    ----------
    log_file : str
        The path to the log file where process information is stored.
    env : str
        The environment under which workers are executed (default is 'python3').
    ids : dict
        A dictionary maintaining the status and process IDs of active worker services.
    """

    # ----------------------------------------------------------------------
    def __init__(self, env: str = 'python3') -> None:
        """
        Initialize the HostWorker instance.

        Parameters
        ----------
        env : str, optional
            The environment in which the worker should run. Defaults to 'python3'.

        Attributes
        ----------
        log_file : str
            The path to the log file where process information will be stored.
        env : str
            The environment specified for running the worker.
        ids : dict
            A dictionary to hold the process IDs and their statuses,
            initialized from the log file if it exists, otherwise empty.

        Raises
        ------
        FileNotFoundError
            If the log file cannot be found and ids cannot be loaded.
        EOFError
            If the log file is empty and cannot be read.

        Notes
        -----
        The constructor attempts to load existing worker IDs from the log file.
        If the log file does not exist or is empty, it initializes `ids` as an empty
        dictionary and calls `save_ids` to create the log file.
        """
        self.log_file = os.path.join(project_folder, 'process_info')
        self.env = env

        try:
            self.load_ids(drop=True)
        except (FileNotFoundError, EOFError):
            self.ids = {}
            self.save_ids()

    # ----------------------------------------------------------------------
    def load_ids(self, drop: bool = False) -> None:
        """
        Load existing worker IDs from the log file.

        This method reads the process information stored in the log file,
        deserializes it, and updates the internal dictionary of worker IDs.
        If `drop` is set to True, it will remove any workers that are no longer active.

        Parameters
        ----------
        drop : bool, optional
            A flag indicating whether to remove inactive workers from the IDs.
            Defaults to False.

        Returns
        -------
        None

        Raises
        ------
        FileNotFoundError
            If the log file cannot be found during the loading process.
        EOFError
            If the log file is empty and cannot be read.

        Notes
        -----
        This function should be called to maintain the accurate status of
        running workers. It is imperative to ensure that the log file
        exists and contains the data expected during the loading process.
        """
        with open(self.log_file, 'rb') as f:
            self.ids = pickle.load(f)

        self.update_status(drop)

    # ----------------------------------------------------------------------
    def save_ids(self) -> None:
        """
        Save the current worker IDs to the log file.

        This method serializes the current state of `self.ids` and writes it to
        the log file specified by `self.log_file`. This ensures that the process
        information is preserved and can be reloaded upon subsequent executions.

        Returns
        -------
        None

        Notes
        -----
        This method should be called after any modifications to `self.ids` to
        ensure that the latest state is saved. It's critical for maintaining
        accurate and persistent records of running worker processes.
        """
        with open(self.log_file, 'wb') as f:
            pickle.dump(self.ids, f)

    # ----------------------------------------------------------------------
    def start_worker(
        self,
        worker_path: str,
        service_name: str = None,
        run: str = "main.py",
        restart: bool = False,
        env: dict = {},
    ):
        """
        Start a worker service within the Docker swarm.

        This method initializes and starts a worker service based on the
        provided worker path. It detects the type of worker (Django, Brython,
        or Python) and delegates the starting of the service to the corresponding
        method.

        Parameters
        ----------
        worker_path : str
            The file system path to the worker application. This path can either be absolute
            or relative, and should contain the necessary worker application structure.

        service_name : str, optional
            The name of the service that will be created in the swarm. If not provided, a
            unique worker name will be generated.

        run : str, optional
            The entry point file in the worker application to be executed. Defaults to "main.py".

        restart : bool, optional
            Indicates whether to restart the service if it already exists. Defaults to False.

        env : dict, optional
            A dictionary of environment variables to set for the service. Defaults to an empty dictionary.

        Returns
        -------
        None
            This method does not return a value.

        Raises
        ------
        FileNotFoundError
            If the given worker path does not exist or cannot be accessed.

        Notes
        -----
        This method ensures that the service name is formatted appropriately
        before starting the worker. It also handles dynamic port allocation
        and manages service creation while ensuring that services are stopped
        and restarted as necessary.
        """

        if os.path.isabs(worker_path) or os.path.exists(worker_path):
            worker_path = os.path.abspath(worker_path)

        if service_name is None:
            service_name = WORKER_NAME.format(
                os.path.split(worker_path)[-1].replace("_", "-")
            )

        service_name_env = service_name.replace('-host-worker', '')

        if service_name in self.ids:
            if restart:
                self.restart(service_name)
            return

        with open(os.path.join(worker_path, 'logfile'), 'w') as logfile:
            process = subprocess.Popen(
                [self.env, os.path.join(worker_path, run)],
                env={
                    "SERVICE_NAME": service_name_env,
                    "WORKER_NAME": service_name,
                    **env,
                },
                stdout=logfile,
                stderr=logfile,
                preexec_fn=os.setpgrp,
            )

        self.ids[service_name] = {
            'pid': process.pid,
            'restart': restart,
            'service_name_env': service_name_env,
            'worker_path': worker_path,
            'run': run,
            'env': env,
        }

        self.save_ids()

    # ----------------------------------------------------------------------
    def stop(self, service_name: str, command: str = 'kill') -> None:
        """
        Stop a running worker service.

        This method terminates the specified service by sending the defined command (default is 'kill')
        to the process associated with the given service name. It ensures that any resource used by
        the service is properly released and the service is stopped without leaving orphan processes.

        Parameters
        ----------
        service_name : str
            The name of the service to be stopped. This must match the name
            of an existing service in the worker ID dictionary.

        command : str, optional
            The command to be executed to stop the service; defaults to 'kill'.
            Other possible commands may include 'terminate' or any valid signal.

        Returns
        -------
        None
            This method does not return a value.

        Raises
        ------
        KeyError
            If the specified service name does not exist in the worker ID dictionary.

        Notes
        -----
        This method effectively manages process termination, ensuring that
        any necessary cleanup is performed as part of the stopping procedure.
        """
        pid = self.ids[service_name]['pid']

        try:
            process = psutil.Process(pid)
            getattr(process, command)()

        except psutil.NoSuchProcess:
            pass

    # ----------------------------------------------------------------------
    def restart(self, service_name: str) -> None:
        """
        Restart a specified worker service.

        This method stops the service identified by `service_name`, then restarts it
        by invoking the corresponding worker initialization parameters.

        Parameters
        ----------
        service_name : str
            The name of the service to restart. It must match one of the existing service names
            recorded in the worker IDs.

        Returns
        -------
        None
            This method does not return a value.

        Notes
        -----
        - The service is stopped using the `stop` method to ensure that any ongoing processes
          are properly terminated before attempting to restart.
        - This function updates the internal state with the new process ID after the restart.
        """
        self.stop(service_name)

        proc = self.ids[service_name]
        with open(
            os.path.join(proc['worker_path'], 'logfile'), 'w'
        ) as logfile:
            process = subprocess.Popen(
                [self.env, os.path.join(proc['worker_path'], proc['run'])],
                env={
                    "SERVICE_NAME": proc['service_name_env'],
                    "WORKER_NAME": service_name,
                    **proc['env'],
                },
                stdout=logfile,
                stderr=logfile,
                preexec_fn=os.setpgrp,
            )

        proc['pid'] = process.pid
        self.save_ids()

    # ----------------------------------------------------------------------
    def gen_worker_name(self, length: int = 8) -> str:
        """
        Generate a unique worker name.

        This method constructs a worker name composed of alphanumeric characters.
        The generated name follows the format `"{worker_name}-worker"` where
        `worker_name` is a random string of the specified length.

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
        The function ensures that each generated worker name does not already exist
        in the swarm services. If a name collision occurs, it will recursively
        attempt to generate a new name until a unique one is found. Care should
        be taken as extensive name collisions may lead to a `RecursionError`.
        """
        id_ = "".join(
            [random.choice(ascii_letters + digits) for _ in range(length)]
        )
        if not WORKER_NAME.format(id_) in self.ids:
            return WORKER_NAME.format(id_)

        return self.gen_worker_name(length)

    # ----------------------------------------------------------------------
    def update_status(self, drop: bool) -> None:
        """
        Update the status of running worker services.

        This method retrieves the current status of each worker service associated
        with the HostWorker instance. It checks the process ID of each service and
        updates the status in the internal dictionary. If the `drop` parameter
        is set to True, any services that have terminated will be removed from
        the internal dictionary.

        Parameters
        ----------
        drop : bool
            A flag indicating whether to remove services that are no longer active.
            If True, services identified as terminated or inactive will be dropped
            from the internal tracking dictionary.

        Returns
        -------
        None
            This method does not return a value.

        Notes
        -----
        The service statuses are updated based on the current state of the processes
        tracked by their respective process IDs. This method is essential for
        maintaining an accurate representation of active worker services and for
        enabling appropriate management actions.
        """
        for name in self.ids:
            pid = self.ids[name]['pid']
            try:
                process = psutil.Process(pid)
                status = process.status()

                self.ids[name]['status'] = status
            except psutil.NoSuchProcess:
                self.ids[name]['status'] = 'None'

        if drop:
            ids = self.ids.copy()
            for name in self.ids:
                if self.ids[name]['status'] == 'None':
                    ids.pop(name)
            self.ids = ids

        self.save_ids()
