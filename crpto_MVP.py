import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os
import logging
load_dotenv()

telegram_token = os.getenv('telegram_token')
telegram_chat_id = os.getenv('telegram_chat_id')
crypto_api_key = os.getenv('crypto_api_key')


def get_coin_info():
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': crypto_api_key,
    }
    params = {
        'start': '1',
        'limit': '10',
        'convert': 'USD'
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    coin_list = []

    for coin in data['data']:
        info = {
            'name': coin['name'],
            'symbol': coin['symbol'],
            'price': coin['quote']['USD']['price'],
            'volume_change_24h': coin['quote']['USD']['volume_change_24h'],
            'percent_change_1h': coin['quote']['USD']['percent_change_1h']
        }
        coin_list.append(info)

    return coin_list


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hey there! Welcome to the *CryptoBot*! I’ll help you stay updated with top crypto stats, alerts, and more. Type `/top_5_coins` to see today's highlights!",
        parse_mode='Markdown'
    )


async def top_5_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin_prices = get_coin_info()
    text = "🚀 *Top 5 Crypto Coins Update!* 🪙💹\n\n"
    alerts = ""

    for i, coin in enumerate(coin_prices[:5], start=1):
        text += (
            f"*{i}. {coin['name']}* ({coin['symbol']})\n"
            f"💰 *Price:* `${coin['price']:.2f}`\n"
            f"📊 *24h Volume Change:* `{coin['volume_change_24h']:.2f}%`\n"
            f"⏱️ *1h Change:* `{coin['percent_change_1h']:.2f}%`\n"
            f"———————————————\n"
        )

        # Alert for large 1h movement
        if abs(coin['percent_change_1h']) > 5:
            alerts += f"⚠️ *{coin['symbol']}* moved `{coin['percent_change_1h']:.2f}%` in the last hour!\n"

        # Price alert for BTC and ETH
        if coin['symbol'] == 'BTC' and coin['price'] > 70000:
            alerts += "🚨 *BTC* just passed $70,000!\n"
        elif coin['symbol'] == 'ETH' and coin['price'] < 2500:
            alerts += "⚠️ *ETH* dropped below $2,500!\n"

    text += "\n🔥 *That's all for now!*\n💎 Stay sharp and keep hustling! 😎💼🚀"

    if alerts:
        text += f"\n\n🚨 *ALERTS:*\n{alerts}"

    await update.message.reply_text(text, parse_mode='Markdown')


def send_telegram_message():
    coin_prices = get_coin_info()
    token = telegram_token
    chat_id = telegram_chat_id

    text = "🚀 *Today's Top 10 Crypto Update!* 🪙💹\n\n"

    for i, coin in enumerate(coin_prices, start=1):
        text += (
            f"*{i}. {coin['name']}* ({coin['symbol']})\n"
            f"💰 *Price:* `${coin['price']:.2f}`\n"
            f"📊 *24h Volume Change:* `{coin['volume_change_24h']:.2f}%`\n"
            f"⏱️ *1h Change:* `{coin['percent_change_1h']:.2f}%`\n"
            f"———————————————\n"
        )

    text += "\n🔥 *That's all for now!*\n💎 Stay sharp and keep hustling! 😎💼🚀"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    res = requests.post(url, data=payload)
    res.raise_for_status()
    print('✅ Message sent to Telegram!')


# create bot
app = ApplicationBuilder().token(telegram_token).build()

# add handlers
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('top_5_coins', top_5_coins))

# run the bot
app.run_polling()
