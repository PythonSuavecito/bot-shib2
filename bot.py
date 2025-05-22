import os
from telegram import Update
from telegram.ext import Application, CommandHandler
import requests
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv('TOKEN_BOT')

async def precio(update: Update, context):
    try:
        # API Bitso with error handling
        def get_data(url):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                return data.get('payload') if data.get('success') else None
            except Exception as e:
                logging.error(f"API call error: {e}")
                return None

        shib_data = get_data('https://api.bitso.com/v3/ticker/?book=shib_usd')
        usd_data = get_data('https://api.bitso.com/v3/ticker/?book=usd_mxn')

        if not shib_data or not usd_data:
            await update.message.reply_text("🔴 Data not available. Try again later")
            return

        # Safe calculations
        precio_shib = float(shib_data['last']) * float(usd_data['last'])
        cambio = float(shib_data.get('change_24', 0))
        
        await update.message.reply_text(
            f"🐕 *SHIB/MXN*: ${precio_shib:,.8f}\n"
            f"📈 *24h*: {cambio:+.2f}%\n"
            f"💵 *100 MXN* = {100/precio_shib:,.0f} SHIB",
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Temporary error. Working on it")

async def start(update: Update, context):
    await update.message.reply_text("👋 SHIB bot activated! Use /precio")

def main():
    app = Application.builder() \
        .token(TOKEN) \
        .concurrent_updates(True) \
        .build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("precio", precio))
    
    # Production configuration for Render
    if os.getenv('ENV') == 'production':
        WEBHOOK_URL = os.getenv('WEBHOOK_URL').replace('http://', 'https://')
        app.run_webhook(
            listen="0.0.0.0",
            port=10000,  # Fixed port for Render
            webhook_url=WEBHOOK_URL,
            secret_token=os.getenv('SECRET_TOKEN'),
            drop_pending_updates=True
        )
    else:
        # Development mode with polling
        app.run_polling()

if __name__ == "__main__":
    main()
