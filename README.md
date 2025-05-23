# Binary Option Trading Bot

This project is a **Binary Option Trading Bot** designed to automate trading on the IQ Option platform. The bot uses technical indicators such as Parabolic SAR, RSI, and Kalman Filter to generate trading signals and execute trades based on predefined strategies.

## Features

- **Automated Trading**: Executes trades on the IQ Option platform based on generated signals.
- **Technical Indicators**:
  - Parabolic SAR
  - RSI (Relative Strength Index)
  - Kalman Filter for price smoothing
- **Progressive Win Streak Strategy**: Adjusts trade amounts dynamically based on win/lose streaks.
- **Telegram Notifications**: Sends updates about trading activity and results via Telegram.
- **Backtesting**: Includes functionality for backtesting strategies with historical data.
- **Trade Logging**: Saves trade logs to CSV files for analysis.

## Requirements

- Python 3.8+
- IQ Option account credentials
- Telegram Bot API token and chat ID
- Required Python libraries:
  - `iqoptionapi`
  - `ta`
  - `pykalman`
  - `pandas`
  - `numpy`
  - `pyautogui`
  - `python-dotenv`
  - `requests`

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/diilanofficial2002/Binary-option-trading-bot.git
   cd Binary-option-trading-bot
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project directory and add the following:

   ```env
   EMAIL=your_email
   PASSWORD=your_password
   BOT_TOKEN=your_telegram_bot_token
   CHAT_ID=your_telegram_chat_id
   ```

## Usage

1. Start the bot by running the main script:

   ```bash
   python execute_bot.py
   ```

2. The bot will:
   - Connect to the IQ Option platform.
   - Fetch market data and apply technical indicators.
   - Generate trading signals and execute trades.
   - Log trade results and send updates via Telegram.

3. Trade logs will be saved as CSV files in the project directory.

## Configuration

- **Trading Pair**: Set the trading pair in the `pair` variable (default: `EURUSD`).
- **Timeframe**: Set the timeframe in minutes in the `timeframe` variable (default: `1`).
- **Target Balance**: Set the target balance in the `target_balance` variable.
- **Initial Trade Amount**: Adjust the percentage of the balance used for the initial trade in the `amount` variable.

## File Structure

- `execute_bot.py`: Main script for running the trading bot.
- `indy/indicator.ipynb`: Notebook for testing and analyzing indicators.
- `test.ipynb`: Notebook for strategy testing and backtesting.

## Disclaimer

This bot is for educational purposes only. Trading binary options involves significant risk, and you may lose all your invested capital. Use this bot at your own risk.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
