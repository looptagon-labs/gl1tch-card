#!/usr/bin/env python3
"""
Test file for GitHubStatsService with GraphQL

This test file demonstrates the async GitHub stats service functionality
using GraphQL API for better performance.
"""

import sys
import os
import asyncio
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from services.github_stats_service import GitHubStatsService


async def test_basic_functionality():
    """Test basic GitHub stats functionality with GraphQL."""
    print("Testing GraphQL GitHub Stats Functionality")
    print("=" * 50)

    # Test with a well-known GitHub user
    service = GitHubStatsService(username="Soumojit28")
    print(f"Testing with user: {service.username}")

    start_time = time.time()
    stats = await service.get_github_stats()
    end_time = time.time()

    if stats:
        print("Successfully fetched GitHub stats!")
        print(f"Username: {stats.user.username}")
        print(f"Name: {stats.user.name}")
        print(f"Bio: {stats.user.bio}")
        print(f"Location: {stats.user.location}")
        print(f"Company: {stats.user.company}")
        print(f"Public Repos: {stats.user.public_repos}")
        print(f"Followers: {stats.user.followers}")
        print(f"Following: {stats.user.following}")
        print(f"Gists: {stats.user.public_gists}")
        print(f"Blog: {stats.user.blog}")
        print(f"Total Stars: {stats.stats.total_stars}")
        print(f"Total Forks: {stats.stats.total_forks}")
        print(f"Total Issues: {stats.stats.total_issues}")
        print(f"Total Pull Requests: {stats.stats.total_pulls}")
        print(f"Total Commits: {stats.stats.total_commits}")
        print(f"Public Repos: {stats.stats.public_repos}")
        print(f"Private Repos: {stats.stats.private_repos}")
        print(f"Public Stars: {stats.stats.public_stars:,}")
        print(f"Private Stars: {stats.stats.private_stars:,}")
        print(f"Account Age (years): {stats.account_age_years}")
        print(f"Top Languages: {stats.github_languages}")
        print(f"Avatar URL: {stats.user.avatar_url}")
        print(f"Execution time: {end_time - start_time:.2f} seconds")
    else:
        print("Failed to fetch GitHub stats")


async def main():
    """Run all tests."""
    print("GitHub Stats Service GraphQL Test Suite")
    print("=" * 60)

    try:
        # Basic functionality test
        await test_basic_functionality()
        print("\nAll tests completed!")

    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        print(f"\nTest suite error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
