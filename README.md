# Oasis Telegram Bot

A Telegram bot that analyzes forwarded messages for potential account compromise and impersonation attempts using OpenAI's GPT models. The bot uses AI-powered function calling to intelligently send alerts to configured API endpoints when potential compromise is detected.

## Features

- Detects potential account compromise in forwarded messages
- Identifies impersonation attempts and scam messages
- Provides detailed analysis and recommendations
- **AI-powered alert system** - the LLM intelligently decides when to send notifications using function calling
- Support for various webhook endpoints (Slack, Discord, custom APIs)
- Simple command interface with `/hello` command

## Setup

### Prerequisites

- Python 3.8+
- Poetry (for dependency management)
- Telegram Bot Token
- OpenAI API Key
- (Optional) API endpoint for receiving alerts

### Installation

1. Install Poetry if you haven't already:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up environment variables:
   ```bash
   export TOKEN="your_telegram_bot_token"
   export OPENAI_API_KEY="your_openai_api_key"
   
   # Alert system configuration (optional)
   export ALERT_API_ENDPOINT="http://localhost:3000/api/alerts"
   ```

## Alert System Configuration

The bot uses OpenAI's function calling feature to intelligently decide when to send alerts. The AI has access to an alert tool that it can choose to use when it detects potential compromise.

### Required
- `ALERT_API_ENDPOINT`: The URL where alerts will be sent (defaults to localhost:3000 if not set)

### Supported Endpoints

The alert system works with various webhook services:

**Slack Webhook:**
```bash
export ALERT_API_ENDPOINT="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
```

**Discord Webhook:**
```bash
export ALERT_API_ENDPOINT="https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK"
```

**Custom API:**
```bash
export ALERT_API_ENDPOINT="http://localhost:3000/api/alerts"
```

### Alert Payload Format

When the AI decides to send an alert, it sends a JSON payload:

```json
{
  "alert_type": "account_compromise",
  "timestamp": 1234567890.123456,
  "compromised_account": "username or name",
  "indicators": "specific reasons for suspicion",
  "recommendation": "what users should do",
  "original_sender": "original message sender",
  "current_sender": "current sender who forwarded",
  "message_content": "the suspicious message content",
  "severity": "high"
}
```

### Running the Bot

You can run the bot in several ways:

**Using Poetry script:**
```bash
poetry run oasis-tg-bot
```

**Using Poetry shell:**
```bash
poetry shell
python bot.py
```

**Direct execution:**
```bash
poetry run python bot.py
```

## Project Structure

```
OasisTgBot/
├── ai.py           # AI analysis and smart alert system
├── bot.py          # Main bot logic
├── decorator.py    # Utility decorators
├── pyproject.toml  # Poetry configuration
├── poetry.lock     # Dependency lock file
└── README.md       # This file
```

## Development

To set up for development:

```bash
poetry install --with dev
```

This installs additional development dependencies including:
- pytest (for testing)
- black (for code formatting)
- flake8 (for linting)

## Usage

1. Start the bot
2. Forward any message to the bot
3. The bot will analyze the forwarded message for signs of compromise
4. **If the AI detects compromise, it will intelligently decide to send an alert to your configured API endpoint**
5. Use `/hello` command to test basic functionality

## How the AI-Powered Alert System Works

1. **Message Analysis**: When a forwarded message is received, OpenAI analyzes it for compromise indicators
2. **Intelligent Decision Making**: The AI uses function calling to decide whether to send an alert based on its analysis
3. **Tool Execution**: If the AI determines an alert is needed, it calls the `send_account_compromise_alert` tool
4. **Alert Delivery**: The system sends an HTTP POST request to your configured endpoint with detailed information
5. **Feedback Loop**: The AI receives confirmation of the alert status and incorporates it into its final response

## AI Function Calling Features

The LLM has access to the following tool:

**`send_account_compromise_alert`**
- **Purpose**: Send alerts when potential account compromise is detected
- **Parameters**: 
  - `compromised_account`: Username/name of compromised account
  - `indicators`: Specific evidence of compromise
  - `recommendation`: Suggested user actions
  - `confidence_level`: Low/Medium/High confidence assessment
- **Smart Decision Making**: The AI only uses this tool when it has sufficient evidence of compromise

## Security Features

- **AI-powered decision making**: Reduces false positives by letting the AI decide when alerts are warranted
- **Confidence levels**: The AI assesses its confidence in compromise detection
- **Timeout protection**: 10-second timeout for API calls
- **Comprehensive error handling and logging**
- **Non-blocking design**: Bot continues working even if alerts fail
- **Function calling validation**: Ensures proper parameters are provided 