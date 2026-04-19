import subprocess
import platform
from typing import Tuple, Optional


class ShellExecutor:
    def __init__(self):
        self.is_linux = platform.system().lower() == "linux"

    def restart_server(self) -> Tuple[int, str, str]:
        return self.run_command('/root/cleaner.sh')

    def memory_info(self) -> Tuple[int, str, str]:
        return self.run_command('free -h')

    def run_command(
            self,
            command: str,
            shell: bool = True,
            timeout: Optional[int] = 30
    ) -> Tuple[int, str, str]:
        if not self.is_linux:
            return -10, "", "Выполнение shell-команд доступно только на Linux сервере"

        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", f"Таймаут ({timeout} сек)"
        except FileNotFoundError:
            return -2, "", f"Файл не найден: {command}"
        except Exception as e:
            return -3, "", f"Ошибка: {str(e)}"