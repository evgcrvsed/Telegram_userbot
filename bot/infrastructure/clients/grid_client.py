import requests
from datetime import datetime, timezone
from typing import Dict, Any

from config.settings import Settings


class GridClient:
    """Клиент для работы с GRID.gg GraphQL API (только запросы)"""

    def __init__(self, settings: Settings):
        self.url = settings.GRID_API_URL
        self.headers = {
            "accept": "application/json, multipart/mixed",
            "content-type": "application/json",
            "x-api-key": settings.GRID_API_KEY,
            "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\"",
            "sec-ch-ua-platform": "\"Windows\"",
            "referrer": "https://portal.grid.gg/",
        }
        self.settings = settings

    def get_todays_matches_raw(self) -> Dict[str, Any]:
        """Возвращает сырые данные о матчах на сегодня"""
        today = datetime.now(timezone.utc).date()
        start_of_day = datetime.combine(today, datetime.min.time(), timezone.utc)
        end_of_day = start_of_day.replace(hour=23, minute=59, second=59)

        payload = {
            "query": f"""
            query GetTodaysMatchTimes {{
              allSeries(
                filter: {{
                  startTimeScheduled: {{
                    gte: "{start_of_day.strftime('%Y-%m-%dT%H:%M:%SZ')}",
                    lte: "{end_of_day.strftime('%Y-%m-%dT%H:%M:%SZ')}"
                  }}
                }}
                first: 50
                orderBy: StartTimeScheduled
                orderDirection: ASC
              ) {{
                edges {{
                  node {{
                    startTimeScheduled
                    teams {{
                      baseInfo {{
                        logoUrl
                        name
                      }}
                    }}
                    tournament {{
                      name
                    }}
                    title {{
                      name
                    }}
                    format {{
                      nameShortened
                    }}
                  }}
                }}
              }}
            }}
            """,
            "operationName": "GetTodaysMatchTimes"
        }

        response = requests.post(self.url, headers=self.headers, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()