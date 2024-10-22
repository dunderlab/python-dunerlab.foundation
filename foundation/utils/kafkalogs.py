"""
============
KafkaLogging
============

This module provides a logging handler that sends log messages to a Kafka topic.

This module defines the `KafkaLogging` class, which extends the standard logging.Handler.
It facilitates logging through Kafka, allowing for the collection and monitoring of log
messages in distributed applications.

Key functionalities include:
- Emitting log messages to a specified Kafka topic.
- Checking the availability of the Kafka producer for logging.

Ensure that the Kafka service is operational and that network configurations permit
communication with the Kafka server for successful logging.
"""

from foundation.radiant.utils import environ
from confluent_kafka import Producer
import logging

level = logging.WARNING


########################################################################
class KafkaLogging(logging.Handler):
    """KafkaLogging is a logging handler that sends log messages to a Kafka topic.

    This class extends the standard logging.Handler to facilitate logging
    via Kafka, enabling the collection and monitoring of log messages in
    a distributed application setting.

    Attributes
    ----------
    topic : str
        The Kafka topic to which log messages are sent. Defaults to 'logs'
        if the 'WORKER_NAME' environment variable is not set.
    producer : confluent_kafka.Producer
        A Kafka producer instance responsible for sending messages to the Kafka
        topic.

    Methods
    -------
    emit(record: logging.LogRecord) -> None
        Emit a log record to the specified Kafka topic.

    kafka_available() -> bool
        Check the availability of the Kafka producer and its ability to list topics.

    Notes
    -----
    Ensure that the Kafka service is operational, and that network configurations permit
    communication with the Kafka server for successful logging.
    """

    # ----------------------------------------------------------------------
    def __init__(self) -> None:
        """Initialize the KafkaLogging handler.

        This constructor sets up the Kafka logging handler by taking environment
        variables for the logging topic, configuring the log message format, and
        establishing a connection to the Kafka producer.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        None

        Notes
        -----
        The default topic will be 'logs' if the 'WORKER_NAME' environment variable is not set.
        """
        super().__init__()

        self.topic = environ('WORKER_NAME', 'logs')
        formatter = logging.Formatter(
            f'%(levelname)s: {self.topic} [%(asctime)s]: %(message)s'
        )
        self.setFormatter(formatter)
        self.producer = Producer(
            {'bootstrap.servers': 'kafka-logs-service:9093'}
        )

    # ----------------------------------------------------------------------
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record.

        This method is invoked when a log record is generated. It formats the
        log record into a message string and sends it to the Kafka topic.

        Parameters
        ----------
        record : logging.LogRecord
            The log record containing information related to the event
            being logged. This includes attributes such as the message,
            severity level, and the time of logging.

        Returns
        -------
        None
            This method does not return a value.

        Notes
        -----
        The log message is produced to the Kafka topic specified by the
        `topic` attribute. Ensure that the Kafka producer is properly
        configured and connected before invoking this method.
        """
        log_message = self.format(record)
        self.producer.produce(self.topic, value=log_message)
        self.producer.flush()

    # ----------------------------------------------------------------------
    @property
    def kafka_available(self) -> bool:
        """Check the availability of the Kafka producer.

        This property checks whether the Kafka producer can connect to the Kafka
        service and retrieve the list of topics. It serves as an indicator of
        the Kafka logging system's operational status.

        Returns
        -------
        bool
            True if the Kafka producer can successfully list topics; False
            otherwise.

        Notes
        -----
        Ensure that the Kafka service is running and accessible. This property
        may raise exceptions if there are connection issues or if the Kafka
        service is not available.
        """
        try:
            self.producer.list_topics(timeout=0.5)
            return True
        except:
            return False


try:
    custom_handler = KafkaLogging()
    if custom_handler.kafka_available:
        custom_handler.setLevel(level)
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.addHandler(custom_handler)
except Exception as e:
    logging.warning('Impossible to connect logging with Kafka')
    logging.warning(str(e))
