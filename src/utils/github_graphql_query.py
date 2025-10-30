"""
GitHub GraphQL Queries

This module contains all GraphQL queries used for fetching GitHub user data.
"""

# Query to fetch comprehensive user stats
USER_STATS_QUERY = """
query($username: String!) {
  user(login: $username) {
    login
    name
    bio
    followers { totalCount }
    following { totalCount }
    createdAt
    updatedAt
    repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: UPDATED_AT, direction: DESC}) {
      totalCount
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        name
        isPrivate
        isFork
        stargazerCount
        forkCount
        primaryLanguage { name }
        createdAt
        updatedAt
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

# Query to fetch additional repositories with pagination
REPOSITORIES_PAGINATION_QUERY = """
query($username: String!, $after: String) {
  user(login: $username) {
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, orderBy: {field: UPDATED_AT, direction: DESC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        name
        isPrivate
        isFork
        stargazerCount
        forkCount
        primaryLanguage { name }
        createdAt
        updatedAt
      }
    }
  }
}
"""
