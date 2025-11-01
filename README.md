# Barry the Bot

A Discord bot designed to enhance and manage roleplaying servers, with a focus on AI-powered tools and activity tracking.

> **Note:** This bot has been migrated to discord.py 2.x with native slash command support. See `MIGRATION_NOTES.md` for technical details.

## Features

-   **AI-Powered Scene Summaries**: Generate "Too Long; Didn't Read" (TL;DR) summaries of roleplay scenes using the Anthropic Claude AI. This requires all participants to opt-in.
-   **AI-Powered Scene Prompts**: Get creative inspiration with D&D scene prompts for solo or two-character scenarios.
-   **Activity Tracking**: Monitor user and channel activity to keep the community vibrant and engaging.
    -   Identify inactive users and channels.
    -   Generate helpful pings for stale roleplay scenes.
-   **Scene Export**: Export roleplay scenes to a text file for easy reading and archiving.
-   **Highly Configurable**: The bot's behaviour can be extensively customised for different servers through the `config.py` file.

## Project Structure

The bot is organised as a Python package with a clear separation between runtime services and Discord extensions. The key pieces are:

-   **`main.py`**: The entry point that loads environment variables, builds the service container, and explicitly loads extensions from `bot/extensions`.
-   **`config.py`**: Centralised server configuration covering monitored channels, role mappings, and thresholds.
-   **`bot/`**: The main package housing production code.
    -   `bot/extensions/`: Slash-command extensions and listeners (`activity.py`, `github_issues.py`, `listeners.py`, `prompts.py`, `summaries.py`).
    -   `bot/services/`: Long-lived service objects such as the GitHub App client.
    -   `bot/core/`: Settings loading and service container wiring.

## Commands

Commands are grouped by their respective extensions.

### Summaries (`bot/extensions/summaries.py`)
-   `/tldr <start_message_id> <end_message_id> [scene_title]`: Summarises a roleplay scene.
-   `/export [start_message_id] [end_message_id]`: Exports a scene to a `.txt` file.

### Prompts (`bot/extensions/prompts.py`)
-   `/scene <character_one_details> <character_two_details> [request]`: Generates a scene prompt for two characters.
-   `/solo <character_details> [request]`: Generates a scene prompt for a single character.
-   `/help`: Displays help information for the AI prompt commands.

### Activity (`bot/extensions/activity.py`)
-   `/useractivity`: Displays a report of user posting activity in monitored roleplay channels (authorised users only).
-   `/channelactivity`: Shows the last post time for all monitored channels and generates a ping message for stale channels (authorised users only).

## Technologies Used

-   [discord.py](https://github.com/Rapptz/discord.py) (v2.x with native slash commands)
-   [Anthropic API](https://www.anthropic.com/): Powers the AI summarisation and prompt generation features.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/lxgrf/barrybot.git
    cd barrybot
    ```

2.  **Install dependencies:**
    The intended operation for this bot is via a Docker container, but if you want to run it locally, you can install the dependencies using `uv`:
    ```
    uv sync
    ```

3.  **Create a `.env` file:**
    Create a file named `.env` in the root directory and add your bot's tokens:
    ```
    discord=YOUR_DISCORD_BOT_TOKEN
    anthropic=YOUR_ANTHROPIC_API_KEY
    ```

4.  **Run the bot:**
    ```bash
    uv run main.py
    ```

## Configuration

The bot is configured via the `config.py` file. Here you can define:
-   Guild (server) specific settings.
-   Monitored channels for activity and summaries.
-   Roles for authorisation and user filtering.
-   Activity thresholds and more.

Refer to the comments in `config.py` for detailed explanations of each setting.

## Testing

BarryBot includes a comprehensive test suite to ensure code quality and prevent regressions.

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
python -m pytest tests/

# Run tests with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

See `tests/README.md` for more detailed testing information.

### Continuous Integration

Tests are automatically run on all pull requests via GitHub Actions. The CI workflow ensures that:
- All unit tests pass
- Configuration is valid
- Code changes don't introduce regressions

## Contributing

For bugs, feature requests, or other contributions, please open an issue or contact the repository owner.
