"""
GitHub Data Models

This module contains data models for GitHub user data and statistics.
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class GitHubUser:
    """Model for GitHub user profile data."""

    username: str
    name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    blog: Optional[str] = None
    public_repos: int = 0
    public_gists: int = 0
    followers: int = 0
    following: int = 0
    created_at: Optional[str] = None
    avatar_url: Optional[str] = None


@dataclass
class RepositoryStats:
    """Model for repository statistics."""

    total_stars: int = 0
    total_forks: int = 0
    total_issues: int = 0
    total_pulls: int = 0
    total_commits: int = 0

    # Public repository stats
    public_repos: int = 0
    public_stars: int = 0
    public_forks: int = 0
    public_issues: int = 0
    public_pulls: int = 0
    public_commits: int = 0

    # Private repository stats
    private_repos: int = 0
    private_stars: int = 0
    private_forks: int = 0
    private_issues: int = 0
    private_pulls: int = 0
    private_commits: int = 0


@dataclass
class CalculatedStats:
    """Intermediate model for calculated repository statistics."""

    total_stars: int
    total_forks: int
    total_issues: int
    total_pulls: int
    total_commits: int
    public_repos: int
    private_repos: int
    public_stars: int
    private_stars: int
    public_forks: int
    private_forks: int
    public_issues: int
    private_issues: int
    public_pulls: int
    private_pulls: int
    public_commits: int
    private_commits: int


@dataclass
class UserProfileData:
    """Intermediate model for user profile data."""

    user_data: dict
    github_languages: List[str]
    account_age: int
    repositories: List[dict]


@dataclass
class GitHubRepository:
    """Model for individual GitHub repository data."""

    name: str
    is_private: bool = False
    stargazer_count: int = 0
    fork_count: int = 0
    issues_count: int = 0
    pull_requests_count: int = 0
    commits_count: int = 0
    primary_language: Optional[str] = None


@dataclass
class GitHubStats:
    """Complete GitHub statistics model."""

    user: GitHubUser
    stats: RepositoryStats
    github_languages: List[str]
    account_age_years: int
    repositories: List[GitHubRepository]
