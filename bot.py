iimport os
from telegram import Update
from telegram.ext import Application, CommandHandler
import requests
import logging

# Configura logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv('TOKEN_BOT')

async def precio(update: Update, context):
    try:
        # API Bitso con manejo de errores
        def get_data(url):
            try:
                response = requests.get(url, timeout=10)
                data = response.json()
                return data.get('payload') if data.get('success') else None
            except:
                return None

        shib_data = get_data('https://api.bitso.com/v3/ticker/?book=shib_usd')
        usd_data = get_data('https://api.bitso.com/v3/ticker/?book=usd_mxn')

        if not shib_data or not usd_data:
            await update.message.reply_text("🔴 Datos no disponibles. Intenta más tarde")
            return

        # Cálculos seguros
        precio_shib = float(shib_data['last']) * float(usd_data['last'])
        cambio = float(shib_data.get('change_24', 0))
        
        await update.message.reply_text(
            f"🐕 *SHIB/MXN*: ${precio_shib:,.8f}\n"
            f"📈 *24h*: {cambio:+.2f}%\n"
            f"💵 *100 MXN* = {100/precio_shib:,.0f} SHIB",
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("⚠️ Error temporal. Ya lo estoy solucionando")

def main():
    app = Application.builder() \
        .token(TOKEN) \
        .concurrent_updates(True) \
        .build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("precio", precio))
    
    # Webhook para Render (opcional)
    if "RENDER" in os.environ:
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 10000)),
            webhook_url=os.getenv("WEBHOOK_URL")
        )
    else:
        app.run_polling()

async def start(update: Update, context):
    await update.message.reply_text("👋 ¡Bot SHIB activado! Usa /precio")

if __name__ == "__main__":
    main()
