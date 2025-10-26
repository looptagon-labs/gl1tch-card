from os import getenv, environ


class EnvironmentManagerService:
    """
    Service class for managing environment variables and configuration settings.

    This class handles the retrieval and validation of environment variables
    used throughout the application.
    """

    # List of string values that should be considered as "true" for boolean parsing
    _TRUTHY = ["true", "1", "t", "y", "yes"]

    # Required API tokens - these will raise KeyError if not provided
    GH_TOKEN = environ["INPUT_GH_TOKEN"]  # type: ignore # GitHub token for API access
    WAKATIME_API_KEY = environ[
        "INPUT_WAKATIME_API_KEY"
    ]  # WakaTime API key for coding stats

    THEME_NAME = getenv("INPUT_THEME_NAME", "Aco")  # Theme name for the card

    # Optional profile field configurations
    FIELD_BIO = getenv("INPUT_FIELD_BIO")  # Bio field content
    FIELD_EMAIL = getenv("INPUT_FIELD_EMAIL")  # Email field content
    FIELD_WEBSITE = getenv("INPUT_FIELD_WEBSITE")  # Website field content (optional)

    # Display toggle settings - control which sections are shown on the card
    SHOW_EDITORS = (
        getenv("INPUT_SHOW_EDITORS", "True").lower() in _TRUTHY
    )  # Show editor usage stats
    SHOW_COMMIT = (
        getenv("INPUT_SHOW_COMMIT", "True").lower() in _TRUTHY
    )  # Show commit activity
    SHOW_LANGUAGE = (
        getenv("INPUT_SHOW_LANGUAGE", "True").lower() in _TRUTHY
    )  # Show language breakdown
    SHOW_LINES_OF_CODE = getenv("INPUT_SHOW_LINES_OF_CODE", "False").lower() in _TRUTHY
