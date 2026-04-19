from telethon import events

from .base_handler import BaseHandler

from infrastructure.logger import UltraLogger
from config.settings import Settings

class InHandler(BaseHandler):
    """Обработчик входящих сообщений (пока заглушка)"""
    def __init__(self, logger: UltraLogger, settings: Settings):
        super().__init__(logger, settings)

    async def handle(self, event: events.NewMessage.Event):
        await self.log_message(event, "← Входящее")

        # Здесь в будущем будет обработка стикеров, команд от других пользователей и т.д.
        # Пока просто логируем
        pass

