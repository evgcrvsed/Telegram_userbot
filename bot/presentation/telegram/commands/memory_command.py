# presentation/telegram/commands/memory_command.py
from datetime import datetime
from .base_command import BaseCommand
from infrastructure.shell_executor import ShellExecutor


class MemoryCommand(BaseCommand):
    def __init__(self, client, logger, settings, shell_executor: ShellExecutor):
        super().__init__(client, logger, settings)
        self.shell_executor = shell_executor

    async def execute(self, event):
        self.logger.info("Команда /memory выполнена")

        await self.reply(event, "🔄 Получаю информацию о системе...")

        code, stdout, stderr = self.shell_executor.memory_info()

        if code != 0:
            error = stderr or stdout or "Неизвестная ошибка"
            await self.reply(event, f"❌ Ошибка получения данных:\n<code>{error}</code>", parse_mode='HTML')
            return

        formatted = self._format_memory_output(stdout)
        await self.reply(event, formatted, parse_mode='HTML')

    @staticmethod
    def _format_memory_output(raw: str) -> str:
        """Отдельный метод форматирования — легко тестировать и менять"""
        lines = [line.strip() for line in raw.strip().split('\n') if line.strip()]

        if len(lines) < 2:
            return "<b>❌ Некорректные данные от free -h</b>"

        result = "<b>🖥️  Состояние памяти и свопа</b>\n\n"

        # Mem
        mem_parts = lines[1].split()
        if len(mem_parts) >= 7:
            total, used, free, shared, buff_cache, available = mem_parts[1:7]

            result += "<b>📊 RAM:</b>\n"
            result += f"├ Общая:      <code>{total}</code>\n"
            result += f"├ Используется: <code>{used}</code>\n"
            result += f"├ Свободно:     <code>{free}</code>\n"
            result += f"├ Shared:       <code>{shared}</code>\n"
            result += f"├ Buff/Cache:   <code>{buff_cache}</code>\n"
            result += f"└ Доступно:     <b><code>{available}</code></b>\n\n"

            # Предупреждение
            try:
                avail_num = float(''.join(c for c in available if c.isdigit() or c == '.'))
                unit = available[-1]
                if (unit == 'G' and avail_num < 2.0) or unit == 'M':
                    result += "⚠️ <b>Внимание: мало доступной оперативной памяти!</b>\n\n"
            except:
                pass

        # Swap
        if len(lines) > 2:
            swap_parts = lines[2].split()
            if len(swap_parts) >= 4:
                result += "<b>🔄 Swap:</b>\n"
                result += f"├ Общий:     <code>{swap_parts[1]}</code>\n"
                result += f"├ Используется: <code>{swap_parts[2]}</code>\n"
                result += f"└ Свободно:     <code>{swap_parts[3]}</code>\n"

        result += f"\n<i>Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        return result