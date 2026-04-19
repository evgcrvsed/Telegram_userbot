import os
from collections import defaultdict
from datetime import datetime
from typing import List, Tuple

from infrastructure.clients.grid_client import GridClient
from infrastructure.logger import UltraLogger
from infrastructure.repositories.json_icon_repository import JsonIconRepository
from config.settings import Settings

from telethon.tl.types import MessageEntityCustomEmoji, MessageEntityBold, MessageEntityUnderline, MessageEntityBlockquote


import requests


class MatchService:
    """Сервис для получения и форматирования расписания матчей"""

    MERGE_RULES = {
        "CCT all regions": ["CCT"],
        "ESEA all regions": ["ESEA"],
    }

    def __init__(
        self,
        grid_client: GridClient,
        logger: UltraLogger,
        settings: Settings,
        db: JsonIconRepository
    ):
        self.grid_client = grid_client
        self.logger = logger
        self.settings = settings
        self.db: JsonIconRepository = db

    def get_matches_for_game(self, game_name: str) -> tuple[str, list]:
        """Возвращает текст расписания + entities (bold, underline, blockquote)"""
        try:
            raw_data = self.grid_client.get_todays_matches_raw()
        except Exception as e:
            self.logger.error(f"Ошибка запроса к GRID: {e}")
            return "❌ Ошибка при получении расписания матчей.", []

        tournaments = defaultdict(list)
        edges = raw_data.get("data", {}).get("allSeries", {}).get("edges", [])

        # Сбор данных
        for edge in edges:
            node = edge["node"]

            if node["title"]["name"] != game_name:
                continue

            tournament_name = node["tournament"]["name"]
            start_time = node["startTimeScheduled"]
            teams = node["teams"]

            team1 = teams[0]["baseInfo"]["name"].strip()
            team2 = teams[1]["baseInfo"]["name"].strip()

            # Скачиваем логотипы
            self._download_logo_if_needed(teams[0]["baseInfo"])
            self._download_logo_if_needed(teams[1]["baseInfo"])

            # Merge правил
            for new_name, keywords in self.MERGE_RULES.items():
                if any(k in tournament_name for k in keywords):
                    tournament_name = new_name
                    break

            if tournament_name in self.settings.IGNORED_TOURNAMENTS:
                continue

            dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
            time_str = dt.strftime("%H:%M")

            tournaments[tournament_name].append((time_str, team1, team2))

        # ====================== Text + Entity Builder (как в оригинале) ======================
        result_text = ""
        formatting_entities = []
        utf16_cursor = 0

        for tournament in sorted(tournaments.keys()):
            # ---------- Tournament header ----------
            tournament_line = f"{self.settings.EMOJI_PASS} {tournament}\n"

            header_start = utf16_cursor + len(self.settings.EMOJI_PASS.encode("utf-16-le")) // 2 + 1
            header_length = len(tournament.encode("utf-16-le")) // 2

            formatting_entities.append(
                MessageEntityBold(offset=header_start, length=header_length)
            )
            formatting_entities.append(
                MessageEntityUnderline(offset=header_start, length=header_length)
            )

            result_text += tournament_line
            utf16_cursor += len(tournament_line.encode("utf-16-le")) // 2

            # ---------- Matches block ----------
            matches_block_start = utf16_cursor

            matches_text = ""
            matches = sorted(tournaments[tournament], key=lambda x: x[0])

            for time_str, team1, team2 in matches:
                match_line = (
                    f"{time_str} — {self.settings.EMOJI_PASS} {team1} vs {self.settings.EMOJI_PASS} {team2}\n"
                )
                matches_text += match_line

            if matches_text:
                # Важный момент из оригинала: убираем последнюю \n для расчёта длины blockquote
                block_text_for_length = matches_text.rstrip("\n")
                block_length = len(block_text_for_length.encode("utf-16-le")) // 2

                formatting_entities.append(
                    MessageEntityBlockquote(
                        offset=matches_block_start,
                        length=block_length
                    )
                )

            result_text += matches_text + "\n"
            utf16_cursor += len((matches_text + "\n").encode("utf-16-le")) // 2

        if len(result_text.strip()) == 0:
            result_text = 'Матчей сегодня нет!'

        return result_text, formatting_entities

    def _download_logo_if_needed(self, team_info: dict):
        """Скачивает логотип команды, если его ещё нет"""
        team_name = team_info["name"].strip()
        logo_path = f"data/logoUrl/{team_name}.png"

        icons_data = self.db.get_data()

        if not os.path.exists(logo_path):
            try:
                icons_data.setdefault(team_name, {})["logoUrl"] = team_info["logoUrl"]
                response = requests.get(team_info["logoUrl"], timeout=10)
                os.makedirs(os.path.dirname(logo_path), exist_ok=True)

                with open(logo_path, "wb") as f:
                    f.write(response.content)

                self.db.set_data(icons_data)
                self.logger.info(f"Скачан логотип для {team_name}")
            except Exception as e:
                self.logger.error(f"Не удалось скачать логотип для {team_name}: {e}")