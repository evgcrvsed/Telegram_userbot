from typing import Dict
from .base_command import BaseCommand
from .memory_command import MemoryCommand
from .restart_command import RestartCommand
from .help_command import HelpCommand


class CommandRegistry:
    """Реестр всех команд — легко добавлять новые без изменения OutHandler"""

    def __init__(self, client, logger, settings, shell_executor, match_service, icon_repo):
        self.commands: Dict[str, BaseCommand] = {
            "/memory": MemoryCommand(client, logger, settings, shell_executor),
            "/restart": RestartCommand(client, logger, settings, shell_executor),
            "/help": HelpCommand(client, logger, settings),
            # "/status", "/logs" и т.д. — просто добавляешь сюда
        }

    async def execute(self, command: str, event):
        cmd = command.strip().lower()
        handler = self.commands.get(cmd)
        if handler:
            await handler.execute(event)
        else:
            # fallback
            await event.reply("Неизвестная команда. Используй /help")