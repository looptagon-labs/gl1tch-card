import aiohttp
import asyncio
import yaml


class ThemeService:
    """Service for fetching theme configurations from Gogh repository."""

    def __init__(self, theme_name: str):
        """Initialize with a theme name."""
        self.theme_name = theme_name

    async def fetch_theme_data(self):
        """Fetch theme YAML data from Gogh repository and parse it."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://raw.githubusercontent.com/Gogh-Co/Gogh/master/themes/{self.theme_name}.yml"
            ) as response:
                theme_data = await response.text()
                return yaml.safe_load(theme_data)


if __name__ == "__main__":
    # Test the service with the "Aco" theme
    theme_service = ThemeService("Aco")
    theme_data = asyncio.run(theme_service.fetch_theme_data())
    print(theme_data)
