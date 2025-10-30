import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import asyncio
from ..utils.github_graphql_query import USER_STATS_QUERY, REPOSITORIES_PAGINATION_QUERY


class GitHubStatsService:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.graphql_url = "https://api.github.com/graphql"

    async def _make_graphql_request(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        """Make a GraphQL request to GitHub API"""
        payload = {"query": query, "variables": variables or {}}
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Content-Type": "application/json",
        }

        try:

            async def _post(s: aiohttp.ClientSession) -> Dict[str, Any]:
                async with s.post(
                    self.graphql_url, headers=headers, json=payload
                ) as response:
                    data = await response.json()
                    if "errors" in data:
                        print(f"GraphQL Errors: {data['errors']}")
                        return {}
                    if response.status != 200:
                        print(f"HTTP Error: {response.status}")
                        return {}
                    return data.get("data", {})

            if session is None:
                async with aiohttp.ClientSession() as temp_session:
                    return await _post(temp_session)
            return await _post(session)
        except Exception as e:
            print(f"Exception during API call: {e}")
            return {}

    def _format_user_info(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Format user information"""
        return {
            "username": user.get("login"),
            "name": user.get("name"),
            "bio": user.get("bio"),
            "followers": user.get("followers", {}).get("totalCount", 0),
            "following": user.get("following", {}).get("totalCount", 0),
            "created_at": user.get("createdAt"),
            "updated_at": user.get("updatedAt"),
        }

    def _format_repository_stats(self, repos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format repository statistics"""
        public_repos = [repo for repo in repos if not repo.get("isPrivate", False)]
        private_repos = [repo for repo in repos if repo.get("isPrivate", False)]
        forks = [repo for repo in repos if repo.get("isFork", False)]

        languages = {}
        for repo in repos:
            primary_language = repo.get("primaryLanguage")
            if primary_language and (language := primary_language.get("name")):
                languages[language] = languages.get(language, 0) + 1

        return {
            "total_repos": len(repos),
            "public_repos": len(public_repos),
            "private_repos": len(private_repos),
            "forks": len(forks),
            "original_repos": len(repos) - len(forks),
            "total_stars": sum(repo.get("stargazerCount", 0) for repo in repos),
            "total_forks": sum(repo.get("forkCount", 0) for repo in repos),
            "languages": dict(sorted(languages.items(), key=lambda item: -item[1])),
            "most_starred_repo": (
                max(repos, key=lambda repo: repo.get("stargazerCount", 0))
                if repos and any(repo.get("stargazerCount", 0) > 0 for repo in repos)
                else None
            ),
        }

    def _format_contribution_stats(
        self, contributions_collection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format contribution statistics"""
        contribution_calendar = contributions_collection.get("contributionCalendar", {})
        weeks = contribution_calendar.get("weeks", [])

        current_streak, longest_streak = self._calculate_streaks(weeks)

        return {
            "total_commit_contributions": contributions_collection.get(
                "totalCommitContributions", 0
            ),
            "total_issue_contributions": contributions_collection.get(
                "totalIssueContributions", 0
            ),
            "total_pr_contributions": contributions_collection.get(
                "totalPullRequestContributions", 0
            ),
            "total_pr_review_contributions": contributions_collection.get(
                "totalPullRequestReviewContributions", 0
            ),
            "total_contributions": contribution_calendar.get("totalContributions", 0),
            "current_streak": current_streak,
            "longest_streak": longest_streak,
        }

    def _calculate_streaks(self, weeks: List[Dict[str, Any]]) -> tuple[int, int]:
        """Calculate current and longest contribution streaks"""
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        today = datetime.now(timezone.utc).date()

        all_days = []
        for week in weeks:
            for day in week.get("contributionDays", []):
                if date_str := day.get("date"):
                    all_days.append(
                        (
                            datetime.fromisoformat(date_str).date(),
                            day.get("contributionCount", 0),
                        )
                    )

        all_days.sort(key=lambda day: day[0])

        for day_date, count in all_days:
            if count > 0:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)

                if day_date <= today:
                    current_streak = temp_streak
            else:
                temp_streak = 0
                if day_date <= today:
                    current_streak = 0

        return current_streak, longest_streak

    async def _fetch_all_repositories(
        self,
        username: str,
        initial_repos: List[Dict[str, Any]],
        page_info: Dict[str, Any],
        session: aiohttp.ClientSession,
    ) -> List[Dict[str, Any]]:
        """Fetch all repositories using pagination"""
        all_repos = initial_repos.copy()
        cursor = page_info.get("endCursor")
        has_next_page = page_info.get("hasNextPage", False)

        while has_next_page and cursor:
            graphql_data = await self._make_graphql_request(
                REPOSITORIES_PAGINATION_QUERY,
                {"username": username, "after": cursor},
                session=session,
            )

            if not graphql_data or "user" not in graphql_data:
                break

            user = graphql_data.get("user", {})
            repos_data = user.get("repositories", {})
            repos = repos_data.get("nodes", [])
            page_info = repos_data.get("pageInfo", {})

            all_repos.extend(repos)
            cursor = page_info.get("endCursor")
            has_next_page = page_info.get("hasNextPage", False)

        return all_repos

    async def get_github_stats(self, username: str) -> Dict[str, Any]:
        try:
            """Get comprehensive GitHub statistics for a user"""
            async with aiohttp.ClientSession() as session:
                graphql_data = await self._make_graphql_request(
                    USER_STATS_QUERY, {"username": username}, session=session
                )

                if not graphql_data or "user" not in graphql_data:
                    print("No data returned from GitHub API")
                    return {}

                user = graphql_data.get("user")
                if not user:
                    print("User data not found in API response")
                    return {}

                repos_data = user.get("repositories", {})
                initial_repos = repos_data.get("nodes", [])
                page_info = repos_data.get("pageInfo", {})

                repos = await self._fetch_all_repositories(
                    username, initial_repos, page_info, session=session
                )

                contributions_collection = user.get("contributionsCollection", {})

                result = {
                    "user_info": self._format_user_info(user),
                    "repository_stats": self._format_repository_stats(repos),
                    "contribution_stats": self._format_contribution_stats(
                        contributions_collection
                    ),
                }
                print(json.dumps(result, indent=2))
                return result
        except Exception as e:
            print(f"Error getting GitHub stats: {e}")
            return {}


if __name__ == "__main__":
    github_token = ""
    test_github = GitHubStatsService(github_token)
    asyncio.run(test_github.get_github_stats("Rishika-dev"))
