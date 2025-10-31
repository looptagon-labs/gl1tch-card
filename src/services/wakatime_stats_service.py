import json
import aiohttp
import asyncio
from models.wakatime_stats_model import WakaStatsResponse, WakaDayData, AllTimeStats


class WakaTimeStatsService:
    def __init__(self, waka_api_key: str):
        self.waka_latest_url = f"https://wakatime.com/api/v1/users/current/stats/last_7_days?api_key={waka_api_key}"
        self.waka_all_url = f"https://wakatime.com/api/v1/users/current/all_time_since_today?api_key={waka_api_key}"

    async def _api_call(self, url: str) -> WakaStatsResponse:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()
                    return WakaStatsResponse(**data)
        except Exception as e:
            print(f"Error calling the API: {e}")
            return WakaStatsResponse(data={})

    def _format_common_stats(self, data: WakaDayData | AllTimeStats) -> dict:
        """Extract common stats that exist in both detailed and all-time data."""
        return {
            "user_id": getattr(data, "user_id", None),
            "timezone": getattr(data, "timezone", None),
            "range": (
                data.range.model_dump()
                if data.range and hasattr(data.range, "model_dump")
                else data.range if data.range else {}
            ),
            "status": getattr(data, "status", None),
            "total_coding_time": data.total_seconds,
            "total_coding_time_text": data.text,
            "daily_average_time": data.daily_average,
            "daily_average_time_text": data.text,
            "percent_calculated": data.percent_calculated,
            "is_up_to_date": data.is_up_to_date,
        }

    def _format_weekly_stats(self, data: WakaDayData) -> dict:
        """Format detailed 7-day stats with breakdowns."""
        return {
            "operating_system": (
                data.operating_systems[0].name if data.operating_systems else None
            ),
            "machine_name": data.machines[0].name if data.machines else None,
            "editor": data.editors[0].name if data.editors else None,
            "most_active_projects": [
                {
                    "project_name": proj.name,
                    "time_spent": proj.total_seconds,
                    "time_spent_text": proj.text,
                    "percentage": proj.percent,
                }
                for proj in data.projects[:5]
            ],
            "language_usage": [
                {
                    "language_name": lang.name,
                    "time_spent": lang.total_seconds,
                    "time_spent_text": lang.text,
                    "percentage": lang.percent,
                }
                for lang in data.languages[:5]
            ],
            "category_usage": [
                {
                    "category_name": cat.name,
                    "time_spent": cat.total_seconds,
                    "time_spent_text": cat.text,
                    "percentage": cat.percent,
                }
                for cat in data.categories
            ],
            "best_day": data.best_day or {},
            "is_stuck": data.is_stuck,
            "days_minus_holidays": data.days_minus_holidays,
            "holidays": data.holidays,
        }

    def _format_all_time_stats(self, data: AllTimeStats) -> dict:
        """Format all-time summary stats."""
        return {
            "stats_type": "all_time_summary",
            "date_range": (
                data.range.model_dump()
                if data.range and hasattr(data.range, "model_dump")
                else {}
            ),
            "all_time_stats": {
                "total_seconds": data.total_seconds,
                "text": data.text,
                "decimal": data.decimal,
                "digital": data.digital,
                "daily_average": data.daily_average,
                "percent_calculated": data.percent_calculated,
                "range": (
                    data.range.model_dump()
                    if data.range and hasattr(data.range, "model_dump")
                    else {}
                ),
                "timeout": data.timeout,
            },
        }

    def _formatter(self, data: WakaDayData | AllTimeStats) -> dict:
        """Format stats data based on type."""
        coding_stats = self._format_common_stats(data)

        if isinstance(data, WakaDayData) and data.projects and data.languages:
            coding_stats.update(self._format_weekly_stats(data))
        elif isinstance(data, AllTimeStats):
            coding_stats.update(self._format_all_time_stats(data))

        return coding_stats

    async def get_waka_time_stats(self):
        week_time, all_time = await asyncio.gather(
            self._api_call(self.waka_latest_url), self._api_call(self.waka_all_url)
        )

        result = {
            "weekly_stats": self._formatter(week_time.data),
            "all_time_stats": self._formatter(all_time.data),
        }
        print(json.dumps(result, indent=2))

        return result


if __name__ == "__main__":
    waka_api_key = ""
    test_waka = WakaTimeStatsService(waka_api_key)
    asyncio.run(test_waka.get_waka_time_stats())
