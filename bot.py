import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler
from dotenv import load_dotenv

# Carga variables de entorno
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context):
    user = update.effective_user
    await update.message.reply_html(
        f"👋 Hola {user.mention_html()}!\n\n"
        "Soy tu <b>bot SHIB profesional</b> 🐕💎\n\n"
        "Usa /precio para ver el valor de SHIB"
    )

async def precio_shib(update: Update, context):
    try:
        response = requests.get("https://api.bitso.com/v3/ticker/?book=shib_mxn")
        data = response.json()
        precio = float(data["payload"]["last"])
        
        # Gráfico emoji dinámico
        tendencia = "📈" if precio > 0.00029 else "📉"
        await update.message.reply_text(
            f"{tendencia} <b>SHIB/MXN:</b> ${precio:,.8f}\n"
            f"🤑 <i>Con $100 puedes comprar: {100/precio:,.0f} SHIB</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"🚨 Error: {str(e)}")

def main():
    # Configuración del bot
    app = Application.builder().token(TOKEN).build()
    
    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("precio", precio_shib))
    
    # Inicia el bot
    app.run_polling()

if __name__ == "__main__":
    main()