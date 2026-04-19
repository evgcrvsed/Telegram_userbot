import logging
from pathlib import Path


class UltraLogger:
    def __init__(self):
        log_dir = Path("data")
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.FileHandler("data/app.log", encoding="utf-8"),
                logging.StreamHandler()
            ]
        )
        self.last_message = None
        self.logger = logging.getLogger("bot")

    def _should_log(self, message: str):
        if message == self.last_message:
            return False
        self.last_message = message
        return True

    def info(self, message: str):
        if self._should_log(message):
            self.logger.info(message, stacklevel=2)

    def error(self, message: str):
        if self._should_log(message):
            self.logger.error(message, stacklevel=2)

    def warning(self, message: str):
        if self._should_log(message):
            self.logger.warning(message, stacklevel=2)

    def debug(self, message: str):
        if self._should_log(message):
            self.logger.debug(message, stacklevel=2)

    def critical(self, message: str):
        if self._should_log(message):
            self.logger.critical(message, stacklevel=2)

    def exception(self, message: str):
        if self._should_log(message):
            self.logger.exception(message, stacklevel=2)