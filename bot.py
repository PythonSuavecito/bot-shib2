import requests
from telegram import Update
from telegram.ext import Application, CommandHandler
import logging

# Configura logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def precio_shib(update: Update, context):
    try:
        # 1. Obtener datos con manejo de errores
        def obtener_datos(par):
            response = requests.get(f"https://api.bitso.com/v3/ticker/?book={par}", timeout=5)
            response.raise_for_status()  # Lanza error si hay problemas HTTP
            data = response.json()
            if not data.get('success', False):
                raise ValueError("API no respondió correctamente")
            return data['payload']
        
        # 2. Obtener ambos precios con reintentos
        try:
            shib_data = obtener_datos("shib_usd")
            usd_data = obtener_datos("usd_mxn")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error de conexión: {e}")
            await update.message.reply_text("🔴 Problema temporal con Bitso. Intenta en 1 minuto")
            return

        # 3. Procesar datos
        precio_shib_usd = float(shib_data["last"])
        precio_usd_mxn = float(usd_data["last"])
        precio_shib_mxn = precio_shib_usd * precio_usd_mxn
        cambio_24h = float(shib_data.get("change_24", 0))

        # 4. Formatear respuesta
        emoji = "📈" if cambio_24h >= 0 else "📉"
        mensaje = (
            f"{emoji} *SHIB/MXN*: `${precio_shib_mxn:,.8f}`\n"
            f"• *24h*: `{cambio_24h:+.2f}%`\n"
            f"• *100 MXN* = `{100/precio_shib_mxn:,.0f} SHIB`\n"
            f"🔄 *Actualizado*: {shib_data['created_at'][11:19]} UTC"
        )
        
        await update.message.reply_text(mensaje, parse_mode="Markdown")

    except Exception as e:
        logging.exception("Error crítico:")
        await update.message.reply_text("⚠️ Error temporal. Estamos trabajando en ello")

def main():
    application = Application.builder().token("7474550148:AAEsCI_WzlsDYxPYAMdwrEASsvUDuNFINT0").build()
    application.add_handler(CommandHandler("precio", precio_shib))
    application.run_polling()

if __name__ == "__main__":
    main()
