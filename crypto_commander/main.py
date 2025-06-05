import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import logging
import os
from dotenv import load_dotenv
load_dotenv()

telegram_token = os.getenv('telegram_token')

# Enable logging
logging.basicConfig(
    filename='crypto_bot.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# CoinGecko API configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

# Dictionary to store user alert preferences
user_alerts = {}

async def get_coin_price(coin_id: str) -> float:
    url = f"{COINGECKO_API_URL}/simple/price"
    params = {'ids': coin_id, 'vs_currencies': 'usd'}
    response = requests.get(url, params=params)
    data = response.json()
    return data[coin_id]['usd']

async def get_top_coins(limit: int = 10) -> list:
    url = f"{COINGECKO_API_URL}/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': limit,
        'page': 1
    }
    response = requests.get(url, params=params)
    return response.json()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = (
        "\U0001F680 *Welcome to Crypto Price Tracker Bot!*\n\n"
        "I can help you track cryptocurrency prices and alerts.\n\n"
        "*Available commands:*\n"
        "/price <coin> - Get current price of a coin\n"
        "/top - Get top 10 cryptocurrencies\n"
        "/alert <coin> <price> - Set a price alert\n"
        "/help - Show help message\n\n"
        "_Example:_\n"
        "/price bitcoin\n"
        "/top\n"
        "/alert ethereum 2500"
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❗ Please specify a coin. Example: /price bitcoin")
        return

    coin_id = context.args[0].lower()
    try:
        price = await get_coin_price(coin_id)
        message = (
            f"\U0001F4B0 *{coin_id.capitalize()} Price*\n\n"
            f"Current price: \${price:,.2f} USD"
        )
        await update.message.reply_text(message, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(f"❌ Could not fetch price for {coin_id}. Please check the coin name.")

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        top_coins = await get_top_coins()
        message = "\U0001F3C6 *Top 10 Cryptocurrencies by Market Cap:*\n\n"
        for i, coin in enumerate(top_coins, 1):
            message += f"{i}. *{coin['name']}* ({coin['symbol'].upper()}) - \${coin['current_price']:,.2f}\n"
        await update.message.reply_text(message, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("❌ Could not fetch top coins. Please try again later.")

async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("❗ Usage: /alert <coin> <target_price>")
        return

    coin_id = context.args[0].lower()
    try:
        target_price = float(context.args[1])
        user_id = update.message.from_user.id

        if user_id not in user_alerts:
            user_alerts[user_id] = []

        user_alerts[user_id].append({
            'coin': coin_id,
            'target_price': target_price,
            'triggered': False
        })

        await update.message.reply_text(
            f"\u23F0 Alert set for *{coin_id}* at \${target_price:,.2f}", parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text("❗ Please enter a valid price number.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "\U0001F4DA *Help Guide:*\n\n"
        "/start - Show welcome message\n"
        "/price <coin> - Get current price of a coin\n"
        "/top - Get top 10 cryptocurrencies\n"
        "/alert <coin> <price> - Set a price alert\n"
        "/help - Show this help message\n\n"
        "_Examples:_\n"
        "/price bitcoin\n"
        "/top\n"
        "/alert ethereum 2500"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def check_alerts(context: ContextTypes.DEFAULT_TYPE):
    for user_id, alerts in user_alerts.items():
        for alert in alerts:
            if not alert['triggered']:
                try:
                    current_price = await get_coin_price(alert['coin'])
                    if (current_price >= alert['target_price'] and current_price <= alert['target_price'] * 1.01) or \
                       (current_price <= alert['target_price'] and current_price >= alert['target_price'] * 0.99):
                        message = (
                            f"\U0001F6A8 *Price Alert!*\n\n"
                            f"{alert['coin'].capitalize()} is now at \${current_price:,.2f}\n"
                            f"Target: \${alert['target_price']:,.2f}"
                        )
                        await context.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
                        alert['triggered'] = True
                except Exception as e:
                    logger.error(f"Error checking alert for {alert['coin']}: {e}")

def main() -> None:
    token = telegram_token
    if not token:
        raise ValueError("BOT_TOKEN not set in environment variables.")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("alert", alert_command))
    application.add_handler(CommandHandler("help", help_command))

    application.job_queue.run_repeating(check_alerts, interval=60.0, first=10.0)

    application.run_polling()

if __name__ == '__main__':
    main()
