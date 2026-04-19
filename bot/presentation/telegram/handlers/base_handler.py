from abc import ABC, abstractmethod
from telethon import events
from telethon import TelegramClient

from infrastructure.logger import UltraLogger
from config.settings import Settings


class BaseHandler(ABC):
    def __init__(self, logger: UltraLogger, settings: Settings):
        self.logger = logger
        self.settings = settings

    async def log_message(self, event: events.NewMessage.Event, direction: str):
        """Общий метод логирования сообщения"""
        chat_id = event.chat_id
        message = event.message
        text = message.text or "[СТИКЕР / МЕДИА / ФАЙЛ]"

        self.logger.info(f"{direction} | Chat: {chat_id} | {text[:100]}")

    @abstractmethod
    async def handle(self, event: events.NewMessage.Event):
        """Каждый обработчик должен реализовать этот метод"""
        pass