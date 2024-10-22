"""
=============
ChaskiLogging
=============

This module provides a logging handler for sending log messages to the Chaski logging service.

The ChaskiLogging class extends the standard logging.Handler to facilitate structured logging
over HTTP. It is designed to enhance monitoring and debugging capabilities by centralizing log
information received from various parts of an application.

Key functionalities include:
- Initialization of the logging handler with configurations derived from environment variables.
- Emission of log records to the Chaski logging service with a specific formatting structure.

Attributes
----------
topic : str
    The logging topic to which log messages are sent. Defaults to 'logs' if the
    'WORKER_NAME' environment variable is not set.
"""

from foundation.radiant.utils import environ
import logging
import requests


########################################################################
class ChaskiLogging(logging.Handler):
    """ChaskiLogging is a logging handler that facilitates logging events to the Chaski logging service.

    This class extends the standard logging.Handler to provide a structured way to handle
    and transmit log messages over HTTP to the Chaski logging service. It is designed to
    improve the monitoring and debugging capabilities of applications by centralizing log
    information.

    Attributes
    ----------
    topic : str
        The logging topic to which log messages are sent. Defaults to 'logs' if the
        'WORKER_NAME' environment variable is not set.

    Methods
    -------
    __init__() -> None
        Initializes the logging handler with the appropriate environment configuration
        and sets the formatting for the log messages.

    emit(record: logging.LogRecord) -> None
        Sends a formatted log message to the configured Chaski logging service.

    Notes
    -----
    The logging format for messages follows the pattern:
    '%(levelname)s: {topic} [%(asctime)s]: %(message)s'.
    This ensures that each log entry includes its severity level,
    the topic, and the timestamp of when the log was generated.
    """

    # ----------------------------------------------------------------------
    def __init__(self) -> None:
        """Initialize the ChaskiLogging handler.

        This constructor sets up the logging handler by taking environment variables
        for the logging topic, configuring the log message format, and establishing
        communication with the Chaski logging service.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Attributes
        ----------
        topic : str
            The logging topic to which log messages are sent. Defaults to 'logs'
            if the 'WORKER_NAME' environment variable is not set.

        Notes
        -----
        The logging format for the messages follows the pattern:
        '%(levelname)s: {topic} [%(asctime)s]: %(message)s'.
        This setup ensures that each log entry includes its severity level,
        the topic, and the timestamp of when the log was generated.
        """
        super().__init__()

        self.topic = environ('WORKER_NAME', 'logs')
        formatter = logging.Formatter(
            f'%(levelname)s: {self.topic} [%(asctime)s]: %(message)s'
        )
        self.setFormatter(formatter)

    # ----------------------------------------------------------------------
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the Chaski logging service.

        This method is invoked when a log record is generated. It formats the log record
        into a message string and sends it to the configured Chaski logging service.

        Parameters
        ----------
        record : logging.LogRecord
            The log record containing information related to the event being logged.
            This includes attributes such as the message, severity level, and the time of logging.

        Returns
        -------
        None
            This method does not return a value.

        Raises
        ------
        Exception
            If an error occurs while sending the log message to the Chaski service,
            an error is logged to the root logger.

        Notes
        -----
        Ensure that the Chaski logging service is reachable and properly configured to handle log messages.
        """
        try:
            log_message = self.format(record)
            params = {
                "topic": self.topic,
                "message": log_message,
            }
            requests.get(
                "http://chaski-api-logger-worker:51115/", params=params
            )

        except Exception as e:
            logging.error(f"Error enviando el log a Chaski: {e}")


try:
    custom_handler = ChaskiLogging()
    custom_handler.setLevel(logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(custom_handler)
except Exception as e:
    logging.warning('Impossible to connect logging with Chaski')
    logging.warning(str(e))
