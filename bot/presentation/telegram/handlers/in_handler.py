from telethon import events
from telethon import TelegramClient

from application.services.match_service import MatchService
from .base_handler import BaseHandler
from .out_handler import OutHandler
from infrastructure.shell_executor import ShellExecutor

from infrastructure.logger import UltraLogger
from config.settings import Settings
from infrastructure.repositories.json_icon_repository import JsonIconRepository

from telethon.tl.types import MessageEntityCustomEmoji, MessageEntityBold, MessageEntityUnderline, MessageEntityBlockquote

class InHandler(BaseHandler):
    """Обработчик входящих сообщений (пока заглушка)"""
    def __init__(
        self,
        client: TelegramClient,
        logger: UltraLogger,
        settings: Settings,
        shell_executor: ShellExecutor,
        match_service: MatchService,
        icon_repo: JsonIconRepository
    ):
        super().__init__(logger, settings)
        self.client = client
        self.shell_executor = shell_executor
        self.match_service = match_service
        self.icon_repo = icon_repo

    async def handle(self, event: events.NewMessage.Event):
        await self.log_message(event, "← Входящее")

        if event.chat_id in self.settings.ALLOWED_CHANNELS_ID:
            print('Оуда')
            await OutHandler._handle_sticker(event)

