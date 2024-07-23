import logging
from logging.handlers import RotatingFileHandler
import os


class Logger:
    def __init__(self, service_name: str):
        self.service_name = service_name
        log_format = f"%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        log_dir = "logs"
        log_file = f"{log_dir}/revspotify.log"

        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)

        # Set up a rotating file handler
        max_file_size = 10 * 1024 * 1024  # 10MB
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_file_size, backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(log_format))

        # Set up a stream handler for console output
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))

        # Get the logger and set the level
        self._logger = logging.getLogger(self.service_name)
        self._logger.setLevel(logging.INFO)
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

        # Prevent the log messages from being duplicated in the python output
        self._logger.propagate = False

    def debug(self, message: str):
        self._logger.debug(message)

    def info(self, message: str):
        self._logger.info(message)

    def warning(self, message: str):
        self._logger.warning(message)

    def error(self, message: str):
        self._logger.error(message)
