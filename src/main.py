"""
This is the main file for the Gl1tch Card Readme Stats action.
"""

import asyncio
import time
import json
from pyfiglet import Figlet
from services.environment_manager_service import EnvironmentManagerService
from services.github_stats_service import GitHubStatsService
from services.wakatime_stats_service import WakaTimeStatsService
from services.theme_service import ThemeService
from services.github_service import GithubService
from services.card_generator_service import CardGeneratorService

env = EnvironmentManagerService()
github_stats = GitHubStatsService(env.GH_TOKEN)
wakatime_stats = WakaTimeStatsService(env.WAKATIME_API_KEY)
github = GithubService(env.GH_TOKEN)
theme = ThemeService(env.THEME_NAME)
f = Figlet(font="banner3-D")


async def main():
    start_time = time.time()
    print(f.renderText("Gl1tch-Card"))
    username = github.get_user()
    # print(username)

    github_stats_data, wakatime_stats_data, theme_data = await asyncio.gather(
        github_stats.get_github_stats(username),
        wakatime_stats.get_waka_time_stats(),
        theme.fetch_theme_data(),
    )

    # print(json.dumps(github_stats_data, indent=2))
    # print(wakatime_stats_data)
    # print(theme_data)

    card_generator = CardGeneratorService(
        github_stats_data, wakatime_stats_data, theme_data
    )
    await card_generator.generate_card("output/card.gif")
    github.update_readme("output/card.gif")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Card generated in {elapsed_time:.2f} seconds")


asyncio.run(main())
