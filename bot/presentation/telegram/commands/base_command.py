from abc import ABC, abstractmethod
from telethon import events
from telethon import TelegramClient

from infrastructure.logger import UltraLogger
from config.settings import Settings


class BaseCommand(ABC):
    def __init__(self, client: TelegramClient, logger: UltraLogger, settings: Settings):
        self.client = client
        self.logger = logger
        self.settings = settings

    @abstractmethod
    async def execute(self, event: events.NewMessage.Event) -> None:
        pass

    async def reply(self, event, text: str, **kwargs):
        await self.client.send_message(event.chat_id, text, **kwargs)