import requests
from telegram import Update
from telegram.ext import Application, CommandHandler
import logging
from datetime import datetime

# Configura logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def precio_shib(update: Update, context):
    try:
        # 1. Obtener datos con triple verificación
        def safe_api_call(url):
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()
                if not data.get('success', False):
                    raise ValueError("API no respondió correctamente")
                return data['payload']
            except Exception as e:
                logging.error(f"Error en API call: {e}")
                return None

        # 2. Intentar máximo 3 veces
        max_retries = 3
        for attempt in range(max_retries):
            shib_data = safe_api_call("https://api.bitso.com/v3/ticker/?book=shib_usd")
            usd_data = safe_api_call("https://api.bitso.com/v3/ticker/?book=usd_mxn")
            
            if shib_data and usd_data:
                break
            elif attempt == max_retries - 1:
                await update.message.reply_text("🔴 Servicio no disponible. Intenta más tarde")
                return

        # 3. Procesar datos con verificación
        try:
            precio_shib = float(shib_data["last"])
            precio_usd = float(usd_data["last"])
            cambio_24h = float(shib_data.get("change_24", 0))
            hora_actualizacion = shib_data.get("created_at", datetime.utcnow().isoformat())
        except KeyError as e:
            logging.error(f"Estructura inesperada: {e}")
            await update.message.reply_text("⚠️ Datos temporales no disponibles")
            return

        # 4. Formatear respuesta
        respuesta = (
            f"🐕 *SHIB/MXN*: ${precio_shib * precio_usd:,.8f}\n"
            f"📈 *24h*: {cambio_24h:+.2f}%\n"
            f"💵 *100 MXN* = {100/(precio_shib * precio_usd):,.0f} SHIB\n"
            f"⏰ *Actualizado*: {hora_actualizacion[11:19]} UTC"
        )
        
        await update.message.reply_text(respuesta, parse_mode="Markdown")

    except Exception as e:
        logging.exception("Error inesperado:")
        await update.message.reply_text("😵 Error crítico. Notificar a mi desarrollador")

def main():
    application = Application.builder().token("7474550148:AAEsCI_WzlsDYxPYAMdwrEASsvUDuNFINT0").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("precio", precio_shib))
    application.run_polling()

async def start(update: Update, context):
    await update.message.reply_text(
        "👋 Hola! Soy tu bot SHIB profesional 🐕💎\n\n"
        "Usa /precio para ver el valor actual"
    )

if __name__ == "__main__":
    main()
