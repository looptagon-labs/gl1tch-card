import aiohttp
from datetime import datetime
from typing import Optional, List
from .environment_manager_service import EnvironmentManagerService
from utils.github_graphql_query import (
    USER_PROFILE_QUERY,
    REPOSITORIES_QUERY,
    GITHUB_GRAPHQL_ENDPOINT,
)
from models.github_stats_models import (
    GitHubStats,
    GitHubUser,
    RepositoryStats,
    GitHubRepository,
    CalculatedStats,
    UserProfileData,
)


class GitHubStatsService:
    """Service for downloading and processing GitHub user data.

    This service provides methods to fetch comprehensive GitHub user statistics,
    including profile information, repository data, and programming language
    analysis.

    Attributes:
        github_headers (dict): Default headers for GitHub API requests
        logger (logging.Logger): Logger instance for the service

    Example:
        >>> service = GitHubStatsService("octocat")
        >>> stats = await service.get_github_stats()
        >>> print(f"User has {stats.stats.total_stars} total stars")
    """

    def __init__(self, username: str, max_repos: int = 1000):
        """Initialize the GitHub Stats Service.

        Args:
            username (str): GitHub username to fetch stats for
            max_repos (int): Maximum number of repositories to fetch (default: 1000)
        """
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")

        if max_repos <= 0:
            raise ValueError("max_repos must be a positive integer")

        self.environment_manager = EnvironmentManagerService()
        github_token = self.environment_manager.GH_TOKEN

        if github_token:
            self.github_headers = {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {github_token}",
            }
        else:
            self.github_headers = {
                "Accept": "application/vnd.github.v3+json",
            }

        self.username = username
        self.max_repos = max_repos

    async def _handle_api_response(
        self, response: aiohttp.ClientResponse
    ) -> dict | list | None:
        """Centralized API response handling with error management."""
        try:
            if response.status != 200:
                error_data = await response.json()
                error_msg = error_data.get("message", "Unknown error")

                if response.status == 403:
                    print(f"Rate limit exceeded: {error_msg}")
                elif response.status == 404:
                    print(f"User not found: {error_msg}")
                else:
                    print(f"API error {response.status}: {error_msg}")

                return None
            return await response.json()
        except Exception as e:
            print(f"Error parsing API response: {e}")
            return None

    async def _fetch_user_data(self, session: aiohttp.ClientSession) -> dict | None:
        """Fetch user profile data using GitHub GraphQL API."""
        try:
            # First, get user basic info and total repo count
            user_query = USER_PROFILE_QUERY

            variables = {"username": self.username}
            payload = {"query": user_query, "variables": variables}

            async with session.post(
                GITHUB_GRAPHQL_ENDPOINT,
                headers=self.github_headers,
                json=payload,
            ) as response:
                result = await self._handle_api_response(response)
                if result and "data" in result and result["data"]["user"]:
                    user_data = result["data"]["user"]
                    all_repos = await self._fetch_all_repositories(
                        session, self.username
                    )
                    user_data["repositories"] = {"nodes": all_repos}
                    return self._transform_graphql_user_data(user_data)
                elif result and "errors" in result:
                    print(f"GraphQL Errors: {result['errors']}")
                return None
        except Exception as e:
            print(f"Error fetching user data: {e}")
            return None

    async def _fetch_all_repositories(
        self, session: aiohttp.ClientSession, username: str
    ) -> list:
        """Fetch all repositories using pagination."""
        all_repos = []
        cursor = None
        has_next_page = True
        page_size = 100

        while has_next_page and len(all_repos) < self.max_repos:
            repos_query = REPOSITORIES_QUERY

            variables = {"username": username, "first": page_size, "after": cursor}
            payload = {"query": repos_query, "variables": variables}

            try:
                async with session.post(
                    GITHUB_GRAPHQL_ENDPOINT,
                    headers=self.github_headers,
                    json=payload,
                ) as response:
                    result = await self._handle_api_response(response)
                    if result and "data" in result and result["data"]["user"]:
                        repos_data = result["data"]["user"]["repositories"]
                        all_repos.extend(repos_data["nodes"])

                        page_info = repos_data["pageInfo"]
                        has_next_page = page_info["hasNextPage"]
                        cursor = page_info["endCursor"]

                        print(
                            f"Fetched {len(repos_data['nodes'])} repos (total: {len(all_repos)})"
                        )

                        # Check if we've reached the max limit
                        if len(all_repos) >= self.max_repos:
                            print(f"Reached max repository limit ({self.max_repos})")
                            break
                    else:
                        break
            except Exception as e:
                print(f"Error fetching repositories page: {e}")
                break

        print(f"Total repositories fetched: {len(all_repos)}")
        return all_repos

    def _build_github_stats_model(
        self,
        user_profile: UserProfileData,
        calculated_stats: CalculatedStats,
    ) -> GitHubStats:
        """Build GitHubStats model from processed data."""

        # Create user model
        user = GitHubUser(
            username=user_profile.user_data.get("login", ""),
            name=user_profile.user_data.get("name"),
            bio=user_profile.user_data.get("bio"),
            location=user_profile.user_data.get("location"),
            company=user_profile.user_data.get("company"),
            blog=user_profile.user_data.get("blog"),
            public_repos=user_profile.user_data.get("public_repos", 0),
            public_gists=user_profile.user_data.get("public_gists", 0),
            followers=user_profile.user_data.get("followers", 0),
            following=user_profile.user_data.get("following", 0),
            created_at=user_profile.user_data.get("created_at"),
            avatar_url=user_profile.user_data.get("avatar_url"),
        )

        # Create repository stats model
        stats = RepositoryStats(
            total_stars=calculated_stats.total_stars,
            total_forks=calculated_stats.total_forks,
            total_issues=calculated_stats.total_issues,
            total_pulls=calculated_stats.total_pulls,
            total_commits=calculated_stats.total_commits,
            public_repos=calculated_stats.public_repos,
            public_stars=calculated_stats.public_stars,
            public_forks=calculated_stats.public_forks,
            public_issues=calculated_stats.public_issues,
            public_pulls=calculated_stats.public_pulls,
            public_commits=calculated_stats.public_commits,
            private_repos=calculated_stats.private_repos,
            private_stars=calculated_stats.private_stars,
            private_forks=calculated_stats.private_forks,
            private_issues=calculated_stats.private_issues,
            private_pulls=calculated_stats.private_pulls,
            private_commits=calculated_stats.private_commits,
        )

        # Create repository models
        repo_models = []
        for repo in user_profile.repositories:
            repo_model = GitHubRepository(
                name=repo.get("name", ""),
                is_private=repo.get("isPrivate", False),
                stargazer_count=repo.get("stargazerCount", 0),
                fork_count=repo.get("forkCount", 0),
                issues_count=repo.get("issues", {}).get("totalCount", 0),
                pull_requests_count=repo.get("pullRequests", {}).get("totalCount", 0),
                commits_count=(
                    repo.get("defaultBranchRef", {})
                    .get("target", {})
                    .get("history", {})
                    .get("totalCount", 0)
                    if repo.get("defaultBranchRef")
                    and repo.get("defaultBranchRef", {}).get("target")
                    else 0
                ),
                primary_language=(
                    repo.get("primaryLanguage", {}).get("name")
                    if repo.get("primaryLanguage")
                    else None
                ),
            )
            repo_models.append(repo_model)

        # Create complete GitHubStats model
        return GitHubStats(
            user=user,
            stats=stats,
            github_languages=user_profile.github_languages,
            account_age_years=user_profile.account_age,
            repositories=repo_models,
        )

    def _transform_graphql_user_data(self, user_data: dict) -> dict:
        """Transform GraphQL user data to match expected format."""
        repos_data = user_data.get("repositories", {}).get("nodes", [])
        total_repos = user_data.get("repositories", {}).get(
            "totalCount", len(repos_data)
        )

        return {
            "login": user_data.get("login"),
            "name": user_data.get("name"),
            "bio": user_data.get("bio"),
            "location": user_data.get("location"),
            "company": user_data.get("company"),
            "blog": user_data.get("websiteUrl"),
            "public_repos": total_repos,
            "public_gists": user_data.get("gists", {}).get("totalCount", 0),
            "followers": user_data.get("followers", {}).get("totalCount", 0),
            "following": user_data.get("following", {}).get("totalCount", 0),
            "created_at": user_data.get("createdAt"),
            "avatar_url": user_data.get("avatarUrl"),
            "repositories": repos_data,
        }

    def _calculate_repo_stats(self, repos_data: list) -> CalculatedStats:
        """Calculate repository statistics from GraphQL data, separating public and private repos.

        Args:
            repos_data (list): List of repository data dictionaries from GraphQL

        Returns:
            CalculatedStats: Dataclass containing all calculated statistics
        """
        try:
            # Separate public and private repositories
            public_repos = [
                repo for repo in repos_data if not repo.get("isPrivate", False)
            ]
            private_repos = [
                repo for repo in repos_data if repo.get("isPrivate", False)
            ]

            # Calculate totals
            total_stars = sum(repo.get("stargazerCount", 0) for repo in repos_data)
            total_forks = sum(repo.get("forkCount", 0) for repo in repos_data)
            total_issues = sum(
                repo.get("issues", {}).get("totalCount", 0) for repo in repos_data
            )
            total_pulls = sum(
                repo.get("pullRequests", {}).get("totalCount", 0) for repo in repos_data
            )
            total_commits = sum(
                (
                    repo.get("defaultBranchRef", {})
                    .get("target", {})
                    .get("history", {})
                    .get("totalCount", 0)
                    if repo.get("defaultBranchRef")
                    and repo.get("defaultBranchRef", {}).get("target")
                    else 0
                )
                for repo in repos_data
            )

            # Calculate public repo stats
            public_stars = sum(repo.get("stargazerCount", 0) for repo in public_repos)
            public_forks = sum(repo.get("forkCount", 0) for repo in public_repos)
            public_issues = sum(
                repo.get("issues", {}).get("totalCount", 0) for repo in public_repos
            )
            public_pulls = sum(
                repo.get("pullRequests", {}).get("totalCount", 0)
                for repo in public_repos
            )
            public_commits = sum(
                (
                    repo.get("defaultBranchRef", {})
                    .get("target", {})
                    .get("history", {})
                    .get("totalCount", 0)
                    if repo.get("defaultBranchRef")
                    and repo.get("defaultBranchRef", {}).get("target")
                    else 0
                )
                for repo in public_repos
            )

            # Calculate private repo stats
            private_stars = sum(repo.get("stargazerCount", 0) for repo in private_repos)
            private_forks = sum(repo.get("forkCount", 0) for repo in private_repos)
            private_issues = sum(
                repo.get("issues", {}).get("totalCount", 0) for repo in private_repos
            )
            private_pulls = sum(
                repo.get("pullRequests", {}).get("totalCount", 0)
                for repo in private_repos
            )
            private_commits = sum(
                (
                    repo.get("defaultBranchRef", {})
                    .get("target", {})
                    .get("history", {})
                    .get("totalCount", 0)
                    if repo.get("defaultBranchRef")
                    and repo.get("defaultBranchRef", {}).get("target")
                    else 0
                )
                for repo in private_repos
            )

            return CalculatedStats(
                total_stars=total_stars,
                total_forks=total_forks,
                total_issues=total_issues,
                total_pulls=total_pulls,
                total_commits=total_commits,
                public_repos=len(public_repos),
                private_repos=len(private_repos),
                public_stars=public_stars,
                private_stars=private_stars,
                public_forks=public_forks,
                private_forks=private_forks,
                public_issues=public_issues,
                private_issues=private_issues,
                public_pulls=public_pulls,
                private_pulls=private_pulls,
                public_commits=public_commits,
                private_commits=private_commits,
            )
        except Exception as e:
            print(f"Error calculating repo stats: {e}")
            return CalculatedStats(
                total_stars=0,
                total_forks=0,
                total_issues=0,
                total_pulls=0,
                total_commits=0,
                public_repos=0,
                private_repos=0,
                public_stars=0,
                private_stars=0,
                public_forks=0,
                private_forks=0,
                public_issues=0,
                private_issues=0,
                public_pulls=0,
                private_pulls=0,
                public_commits=0,
                private_commits=0,
            )

    def _extract_languages(self, repos_data: list, top_n: int = 5) -> list[str]:
        """Extract and rank programming languages from GraphQL repository data.

        Args:
            repos_data (list): List of repository data dictionaries from GraphQL
            top_n (int, optional): Number of top languages to return. Defaults to 5.

        Returns:
            list[str]: List of top programming languages by frequency
        """
        try:
            github_languages = {}
            for repo in repos_data:
                # GraphQL returns language in primaryLanguage.name
                lang_data = repo.get("primaryLanguage")
                if lang_data and lang_data.get("name"):
                    lang = lang_data["name"]
                    github_languages[lang] = github_languages.get(lang, 0) + 1
            # Sort by frequency and get top languages
            github_top_langs = sorted(
                github_languages.items(), key=lambda x: x[1], reverse=True
            )[:top_n]
            return [lang[0] for lang in github_top_langs]
        except Exception as e:
            print(f"Error extracting languages: {e}")
            return []

    def _calculate_account_age(self, user_data: dict) -> int:
        """Calculate account age in years.

        Args:
            user_data (dict): User profile data from GitHub API

        Returns:
            int: Account age in years
        """
        try:
            created_at = user_data.get("created_at", "2020-01-01")
            created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            return datetime.now().year - created_date.year
        except Exception as e:
            print(f"Error calculating account age: {e}")
            return 0

    async def get_github_stats(self) -> Optional[GitHubStats]:
        """Fetch comprehensive GitHub statistics for a user.

        This method orchestrates the fetching and processing of GitHub user data,
        including profile information, repository statistics, and programming
        language analysis.

        Args:
            session (aiohttp.ClientSession): HTTP session for async requests

        Returns:
            dict | None: Comprehensive user profile with GitHub statistics,
                        or None if an error occurs during fetching

        Example:
            >>> downloader = GitHubStatsService("octocat")
            >>> stats = downloader.get_github_stats()
            >>> print(stats["followers"])
            20349

        Note:
            This method makes multiple API calls to GitHub and may take some time
            to complete depending on the number of repositories.
        """
        try:
            # Fetch data using GraphQL (user + repos in one request)
            async with aiohttp.ClientSession() as session:
                user_data = await self._fetch_user_data(session)

                # Check if we got valid data
                if not user_data:
                    print("Failed to fetch user data")
                    return None

                # Extract repositories from user data
                repos_data = user_data.get("repositories", [])
                if not repos_data:
                    print("No repositories found")
                    repos_data = []

                # Calculate statistics
                calculated_stats = self._calculate_repo_stats(repos_data)
                github_languages = self._extract_languages(repos_data)
                account_age = self._calculate_account_age(user_data)

                # Create user profile data
                user_profile = UserProfileData(
                    user_data=user_data,
                    github_languages=github_languages,
                    account_age=account_age,
                    repositories=repos_data,
                )

                return self._build_github_stats_model(
                    user_profile=user_profile,
                    calculated_stats=calculated_stats,
                )

        except Exception as e:
            print(f"Error fetching GitHub stats: {e}")
            return None
