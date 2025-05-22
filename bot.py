import os
from telegram import Update
from telegram.ext import Application, CommandHandler

TOKEN = os.getenv('TOKEN_BOT')
IS_RENDER = os.getenv('RENDER') == 'true'

async def start(update: Update, context):
    await update.message.reply_text('¡Bot SHIB activado! 💎')

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    if IS_RENDER:
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", 10000)),
            webhook_url=os.getenv("WEBHOOK_URL"),
            secret_token='MISECRETO123'
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
