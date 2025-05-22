import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler
from dotenv import load_dotenv
import logging
# Configura logging para ver errores
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
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
        # 1. Obtener datos de la API con manejo de errores
        def get_bitso_data(pair):
            response = requests.get(f"https://api.bitso.com/v3/ticker/?book={pair}")
            data = response.json()
            if not data.get('success', False):
                raise ValueError(f"API no respondió correctamente para {pair}")
            return data['payload']
        
        # 2. Obtener ambos precios
        shib_data = get_bitso_data("shib_usd")
        usd_data = get_bitso_data("usd_mxn")
        
        # 3. Calcular precios
        precio_shib_usd = float(shib_data["last"])
        precio_usd_mxn = float(usd_data["last"])
        precio_shib_mxn = precio_shib_usd * precio_usd_mxn
        cambio_24h = float(shib_data["change_24"])
        
        # 4. Formatear mensaje con emojis
        emoji_tendencia = "📈" if cambio_24h >= 0 else "📉"
        mensaje = (
            f"{emoji_tendencia} *SHIB/MXN*: `${precio_shib_mxn:,.8f}`\n"
            f"• *Cambio 24h*: `{cambio_24h:+.2f}%`\n"
            f"• *Equivalencia*: `100 MXN = {100/precio_shib_mxn:,.0f} SHIB`\n"
            f"🔄 Actualizado: {shib_data['created_at'][11:19]} UTC"
        )
        
        await update.message.reply_text(mensaje, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        await update.message.reply_text("🔴 *Error al obtener datos*:\n\n"
                                      "Estoy teniendo problemas para conectarme con Bitso. "
                                      "Intenta de nuevo en unos minutos.", 
                                      parse_mode="Markdown")

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


    from fastapi import FastAPI
import uvicorn

# Crea servidor web para Render
web_app = FastAPI()

@web_app.get("/")
def home():
    return {"status": "Bot SHIB activo"}

if __name__ == "__main__":
    # Inicia el bot y el servidor web
    import threading
    threading.Thread(target=lambda: uvicorn.run(web_app, host="0.0.0.0", port=10000)).start()
    main()  # Tu función principal del bot