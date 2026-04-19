import json
import os
from typing import Dict, Any

from config.settings import Settings


class JsonIconRepository:
    """Репозиторий для хранения данных об иконках/эмодзи команд (JSON-based)"""

    def __init__(self, settings: Settings):
        self.path = settings.ICONS_JSON_PATH
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self.set_data({})

    def get_data(self) -> Dict[str, Any]:
        """Получить все данные из JSON"""
        with open(self.path, "r", encoding='utf-8') as file:
            return json.load(file)

    def set_data(self, data: Dict[str, Any]):
        """Сохранить данные в JSON"""
        with open(self.path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def get_emoji(self, team_name: str) -> int | None:
        """Получить emoji_id команды"""
        data = self.get_data()
        team_data = data.get(team_name)
        if team_data and team_data.get("emoji"):
            return int(team_data["emoji"])
        return None

    def save_emoji(self, team_name: str, emoji_id: int):
        """Сохранить emoji для команды"""
        data = self.get_data()
        if team_name not in data:
            data[team_name] = {"logoUrl": "", "emoji": ""}

        data[team_name]["emoji"] = str(emoji_id)
        self.set_data(data)

    def ensure_team_exists(self, team_name: str, logo_url: str = ""):
        """Убедиться, что команда есть в базе"""
        data = self.get_data()
        if team_name not in data:
            data[team_name] = {"logoUrl": logo_url, "emoji": ""}
            self.set_data(data)