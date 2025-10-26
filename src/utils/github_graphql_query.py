"""
GitHub GraphQL Queries

This module contains all GraphQL queries used for fetching GitHub user data.
"""

# Query to fetch user profile data
USER_PROFILE_QUERY = """
query($username: String!) {
    user(login: $username) {
        login
        name
        bio
        location
        company
        websiteUrl
        gists {
            totalCount
        }
        followers {
            totalCount
        }
        following {
            totalCount
        }
        createdAt
        avatarUrl
        repositories {
            totalCount
        }
    }
}
"""

# Query to fetch repositories with pagination
REPOSITORIES_QUERY = """
query($username: String!, $after: String, $first: Int!) {
    user(login: $username) {
        repositories(first: $first, after: $after, orderBy: {field: UPDATED_AT, direction: DESC}) {
            pageInfo {
                hasNextPage
                endCursor
            }
            nodes {
                name
                isPrivate
                stargazerCount
                forkCount
                issues {
                    totalCount
                }
                pullRequests {
                    totalCount
                }
                defaultBranchRef {
                    target {
                        ... on Commit {
                            history {
                                totalCount
                            }
                        }
                    }
                }
                primaryLanguage {
                    name
                }
            }
        }
    }
}
"""

# GraphQL endpoint URL
GITHUB_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
