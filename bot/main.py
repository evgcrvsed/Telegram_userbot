import asyncio
import os

from telethon import TelegramClient, events

from config.settings import Settings
from infrastructure.logger import UltraLogger
from infrastructure.shell_executor import ShellExecutor

# PortalGrid компоненты
from infrastructure.clients.grid_client import GridClient
from application.services.match_service import MatchService
from infrastructure.repositories.json_icon_repository import JsonIconRepository

# Telegram handlers
from presentation.telegram.handlers.out_handler import OutHandler
from presentation.telegram.handlers.in_handler import InHandler
from presentation.telegram.handlers.handler_router import HandlerRouter

# FastAPI
from presentation.fastapi.icons_api import app as fastapi_app
import uvicorn


async def start_telegram(client: TelegramClient, logger: UltraLogger):
    """Запуск Telegram бота"""
    await client.start()
    logger.info("Telegram бот успешно запущен!")
    me = await client.get_me()
    logger.info(f"Аккаунт: {me.username or me.id} (ID: {me.id})")
    await client.run_until_disconnected()


async def start_fastapi():
    """Запуск FastAPI сервера"""
    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,  # отключаем reload в production
    )
    server = uvicorn.Server(config)

    # Важно: используем lifespan вместо прямого serve в некоторых случаях
    await server.serve()


async def main():
    # === Сборка всех зависимостей ===
    settings = Settings()
    logger = UltraLogger()

    client = TelegramClient(
        'data/userbot_session',
        settings.API_ID,
        settings.API_HASH
    )

    shell_executor = ShellExecutor()
    grid_client = GridClient(settings)
    icon_repo = JsonIconRepository(settings)

    match_service = MatchService(
        grid_client=grid_client,
        logger=logger,
        settings=settings,
        db=icon_repo
    )

    out_handler = OutHandler(
        client=client,  # важно передавать client
        logger=logger,
        settings=settings,
        shell_executor=shell_executor,
        match_service=match_service,
        icon_repo=icon_repo
    )

    in_handler = InHandler(logger=logger, settings=settings)
    router = HandlerRouter(out_handler=out_handler, in_handler=in_handler)

    # Регистрация обработчика сообщений
    @client.on(events.NewMessage())
    async def message_handler(event: events.NewMessage.Event):
        try:
            await router.handle(event)
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")

    # Создаём необходимые папки
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/logoUrl', exist_ok=True)

    # === Запуск двух сервисов параллельно ===
    logger.info("Запускаем Telegram бота и FastAPI сервер...")

    await asyncio.gather(
        start_telegram(client, logger),
        start_fastapi(),
        return_exceptions=True  # чтобы один сбой не убивал другой
    )


if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("Бот остановлен пользователем.")
            break
        except Exception as e:
            print(f"Критическая ошибка в главном цикле: {e}")
            asyncio.sleep(5)