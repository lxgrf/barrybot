# AI Suggester

A Discord bot designed to enhance and manage roleplaying servers, with a focus on AI-powered tools and activity tracking.

## Features

-   **AI-Powered Scene Summaries**: Generate "Too Long; Didn't Read" (TL;DR) summaries of roleplay scenes using the Anthropic Claude AI. This requires all participants to opt-in.
-   **AI-Powered Scene Prompts**: Get creative inspiration with D&D scene prompts for solo or two-character scenarios.
-   **Activity Tracking**: Monitor user and channel activity to keep the community vibrant and engaging.
    -   Identify inactive users and channels.
    -   Generate helpful pings for stale roleplay scenes.
-   **Scene Export**: Export roleplay scenes to a text file for easy reading and archiving.
-   **Highly Configurable**: The bot's behavior can be extensively customized for different servers through the `config.py` file.

## Commands

### AI & Creative
-   `/tldr <start_message_id> <end_message_id> [scene_title]`: Summarizes a roleplay scene.
-   `/scene <character_one_details> <character_two_details> [request]`: Generates a scene prompt for two characters.
-   `/solo <character_details> [request]`: Generates a scene prompt for a single character.
-   `/export [start_message_id] [end_message_id]`: Exports a scene to a `.txt` file.
-   `/help`: Displays help information for the AI prompt commands.

### Moderation & Activity
-   `/useractivity`: Displays a report of user posting activity in monitored roleplay channels (authorised users only).
-   `/channelactivity`: Shows the last post time for all monitored channels and generates a ping message for stale channels (authorised users only).

## Technologies Used

-   [discord.py](https://github.com/Rapptz/discord.py)
-   [discord-py-slash-command](https://github.com/eunwoo1104/discord-py-slash-command)
-   [Anthropic API](https://www.anthropic.com/): Powers the AI summarization and prompt generation features.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/ai-suggester.git
    cd ai-suggester
    ```

2.  **Install dependencies:**
    ```
    uv sync
    ```
    Though note that the intended operation is through a docker container.

3.  **Create a `.env` file:**
    Create a file named `.env` in the root directory and add your bot's tokens:
    ```
    discord=YOUR_DISCORD_BOT_TOKEN
    anthropic=YOUR_ANTHROPIC_API_KEY
    ```

4.  **Run the bot:**
    ```bash
    python main.py
    ```

## Configuration

The bot is configured via the `config.py` file. Here you can define:
-   Guild (server) specific settings.
-   Monitored channels for activity and summaries.
-   Roles for authorization and user filtering.
-   Activity thresholds and more.

Refer to the comments in `config.py` for detailed explanations of each setting.

## Contributing

For bugs, feature requests, or other contributions, please contact the repository owner.
