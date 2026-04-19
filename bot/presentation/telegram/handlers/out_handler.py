from telethon import events
from telethon import TelegramClient

from application.services.match_service import MatchService
from .base_handler import BaseHandler
from infrastructure.shell_executor import ShellExecutor

from infrastructure.logger import UltraLogger
from config.settings import Settings
from infrastructure.repositories.json_icon_repository import JsonIconRepository

from telethon.tl.types import MessageEntityCustomEmoji, MessageEntityBold, MessageEntityUnderline, MessageEntityBlockquote

class OutHandler(BaseHandler):
    """Обработчик исходящих сообщений"""

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
        self.match_service = match_service  # сервис матчей
        self.icon_repo = icon_repo  # репозиторий эмодзи

    async def handle(self, event: events.NewMessage.Event):
        await self.log_message(event, "→ Исходящее")

        message = event.message

        # Обработка текстовых команд
        if message.text:
            cmd = message.text.strip().lower()

            if cmd == '/restart':
                await self._handle_restart(event)
            elif cmd == '/memory':
                await self._handle_memory_info(event)
            elif cmd == '/help':
                await self._handle_help(event)
            return

        # Обработка стикеров (основная функция бота)
        if message.sticker:
            await self._handle_sticker(event)

    async def _handle_restart(self, event: events.NewMessage.Event):
        self.logger.info("Команда /restart получена")

        await self.client.send_message(event.chat_id, "🔄 Запуск перезагрузки...")

        code, stdout, stderr = self.shell_executor.restart_server()

        if code == 0:
            await self.client.send_message(event.chat_id, stdout)
        else:
            error = stderr or stdout or "Неизвестная ошибка"
            await self.client.send_message(
                event.chat_id, f"❌ {error}"
            )

    async def _handle_help(self, event: events.NewMessage.Event):
        help_text = (
            "<b>🤖 Доступные команды:</b>\n\n"
            "💠 <code>/restart</code> — перезапустить сервер\n"
            "💠 <code>/memory</code> — проверка памяти\n"
            "💠 <code>/help</code> — показать справку"
        )
        await self.client.send_message(event.chat_id, help_text, parse_mode='HTML')

    async def _handle_memory_info(self, event: events.NewMessage.Event):
        self.logger.info("Команда /memory получена")

        await self.client.send_message(event.chat_id, "🔄 Запуск memory...")

        code, stdout, stderr = self.shell_executor.memory_info()

        if code == 0:
            await self.client.send_message(event.chat_id, stdout)
        else:
            error = stderr or stdout or "Неизвестная ошибка"
            await self.client.send_message(
                event.chat_id, f"❌ {error}"
            )

    async def _handle_sticker(self, event: events.NewMessage.Event):
        sticker_id = str(event.message.sticker.id)

        if sticker_id in self.settings.CSGO_STICKERS:
            game_name = self.settings.CSGO_NAME
            # await self.client.send_message(event.chat_id, "🎮 Загружаю расписание CS2...")
        elif sticker_id in self.settings.DOTA2_STICKERS:
            game_name = self.settings.DOTA2_NAME
            # await self.client.send_message(event.chat_id, "🎮 Загружаю расписание Dota 2...")
        else:
            return

        # Получаем уже отформатированный текст + entities
        text, entities = self.match_service.get_matches_for_game(game_name)

        # Заменяем обычные эмодзи на кастомные
        final_text, final_entities = self._replace_emojis(text, entities)

        await self.client.send_message(
            event.chat_id,
            final_text,
            formatting_entities=final_entities
        )

    def _replace_emojis(self, text: str, existing_entities: list) -> tuple[str, list]:
        """Заменяет 😎 на кастомные эмодзи, сохраняя существующее форматирование"""
        new_entities = existing_entities.copy()
        search_pos = 0

        while True:
            pos = text.find(self.settings.EMOJI_PASS, search_pos)
            if pos == -1:
                break

            start = pos + len(self.settings.EMOJI_PASS)
            end = text.find(" vs ", start)
            if end == -1:
                end = text.find("\n", start)
            if end == -1:
                end = len(text)

            team_name = text[start:end].strip()

            emoji_id = self.icon_repo.get_emoji(team_name) or self.settings.EMOJI_EMPTY

            new_entities.append(
                MessageEntityCustomEmoji(
                    offset=pos,
                    length=len(self.settings.EMOJI_PASS),
                    document_id=emoji_id
                )
            )

            search_pos = pos + 1

        return text, new_entities