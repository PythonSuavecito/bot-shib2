import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler
import threading
import logging
from statistics import mean
from datetime import datetime

# Configuración de logging profesional
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('shib_bot.log'),
        logging.StreamHandler()
    ]
)

# Constantes configurables
MAX_HISTORIAL = 15  # Aumentado para mejor análisis
TIMEOUT_API = 8     # Tiempo de espera para APIs
HEALTH_CHECK_MIN = 3 # Minutos entre health checks

# Variables globales seguras
historial_precios = []
token = os.getenv('TOKEN_BOT')

def calcular_ema(prices, period):
    """Calcula la media móvil exponencial"""
    if len(prices) < period:
        return mean(prices) if prices else 0
    
    multiplier = 2 / (period + 1)
    ema = mean(prices[:period])
    
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    
    return ema

class ShibTradingBot:
    def __init__(self):
        self.last_update = datetime.now()
        self.health_check_active = False

    async def start(self, update: Update, context):
        """Maneja el comando /start con un menú interactivo"""
        welcome_msg = (
            "👋 *Bienvenido al SHIB Trading Bot*\n\n"
            "📊 *Comandos disponibles:*\n"
            "/precio - Muestra gráfico y análisis\n"
            "/estrategia - Recomendación de trading\n"
            "/ayuda - Muestra esta ayuda\n\n"
            "🔔 Usa /estrategia para recibir señales automáticas"
        )
        await update.message.reply_text(welcome_msg, parse_mode="Markdown")

    async def get_shib_data(self, retries=1):
        """Obtiene datos de SHIB de Bitso con manejo robusto de errores"""
        endpoints = [
            "https://api.bitso.com/v3/ticker/?book=shib_usd",
            "https://api.bitso.com/v3/ticker/?book=usd_mxn"
        ]
        
        for attempt in range(retries):
            try:
                responses = []
                for url in endpoints:
                    response = requests.get(url, timeout=TIMEOUT_API)
                    response.raise_for_status()
                    data = response.json()
                    if not data.get('success'):
                        raise ValueError(f"API no respondió correctamente: {url}")
                    responses.append(data)
                
                return {
                    'shib_usd': responses[0]['payload'],
                    'usd_mxn': responses[1]['payload'],
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"Error al obtener datos: {str(e)}", exc_info=True)
                    return None
                await asyncio.sleep(1)

    async def precio_shib(self, update: Update, context):
        """Muestra el precio actual con gráfico de tendencia"""
        try:
            data = await self.get_shib_data()
            if not data:
                await update.message.reply_text("⚠️ Error temporal con la API Bitso")
                return

            precio = float(data['shib_usd']['last']) * float(data['usd_mxn']['last'])
            cambio_24h = float(data['shib_usd'].get('change_24', 0))
            
            # Actualizar historial de precios
            historial_precios.append(precio)
            if len(historial_precios) > MAX_HISTORIAL:
                historial_precios.pop(0)
            
            # Generar gráfico de tendencia
            grafico = self.generar_grafico_tendencia(precio, cambio_24h)
            
            respuesta = (
                f"📈 *SHIB/MXN: ${precio:,.8f}*\n"
                f"🔄 24h: {cambio_24h:+.2f}%\n"
                f"📊 Tendencia:\n{grafico}\n"
                f"🕒 Actualizado: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            await update.message.reply_text(respuesta, parse_mode="Markdown")
            
        except Exception as e:
            logging.error(f"Error en precio_shib: {str(e)}", exc_info=True)
            await update.message.reply_text("❌ Error al procesar tu solicitud")

    def generar_grafico_tendencia(self, precio_actual, cambio_24h):
        """Genera un gráfico ASCII basado en el historial"""
        if not historial_precios:
            return "📊 Recolectando datos..."
            
        min_p = min(historial_precios)
        max_p = max(historial_precios)
        rango = max_p - min_p if max_p != min_p else 0.000001
        
        grafico = ""
        for precio in historial_precios[-10:]:  # Mostrar últimos 10 puntos
            proporcion = (precio - min_p) / rango
            barra = "🟢" * int(proporcion * 10) + "🔴" * (10 - int(proporcion * 10))
            grafico += f"{barra} ${precio:,.8f}\n"
        
        return grafico

    async def estrategia_trading(self, update: Update, context):
        """Proporciona recomendaciones de trading basadas en análisis técnico"""
        try:
            data = await self.get_shib_data(retries=3)
            if not data or len(historial_precios) < 5:
                await update.message.reply_text("📊 Recolectando datos...")
                return

            # Datos básicos
            precio = float(data['shib_usd']['last']) * float(data['usd_mxn']['last'])
            high = float(data['shib_usd']['high']) * float(data['usd_mxn']['last'])
            low = float(data['shib_usd']['low']) * float(data['usd_mxn']['last'])
            cambio = float(data['shib_usd'].get('change_24', 0))
            volumen_24h = float(data['shib_usd'].get('volume', 0))
            
            # Análisis técnico combinado
            mm5 = mean(historial_precios[-5:])
            mm10 = mean(historial_precios[-10:]) if len(historial_precios) >= 10 else mm5
            ema10 = calcular_ema(historial_precios, 10)
            volatilidad = ((high - low) / precio) * 100
            
            # Lógica de trading mejorada
            if (precio < ema10 * 0.98 and 
                precio < mm5 * 0.997 and 
                mm5 > mm10 and 
                volumen_24h > 1_000_000):
                accion = "✅ COMPRAR (Retroceso con volumen)"
                sl = precio * 0.94  # -6%
                tp = precio * 1.10  # +10%
            elif (precio > ema10 * 1.15 or 
                  (precio > mm5 * 1.003 and mm5 < mm10)):
                accion = "💰 VENDER (Sobrecompra)"
                sl = precio * 1.03  # +3%
                tp = precio * 0.97  # -3%
            else:
                accion = "🔄 ESPERAR (Sin señal clara)"
                sl = tp = None
            
            # Construir respuesta detallada
            respuesta = (
                f"🔥 *SHIB/MXN - Estrategia Mejorada*\n\n"
                f"📊 Precio: ${precio:,.8f}\n"
                f"📈 MM5: ${mm5:,.8f}\n"
                f"📉 MM10: ${mm10:,.8f}\n"
                f"📊 EMA10: ${ema10:,.8f}\n"
                f"🌪 Volatilidad: {volatilidad:.2f}%\n"
                f"💸 Volumen 24h: ${volumen_24h:,.2f} USD\n\n"
                f"🚨 *Señal:* {accion}"
            )
            
            if sl and tp:
                respuesta += (
                    f"\n\n⚡ *Gestión de Riesgo*\n"
                    f"🛑 Stop-loss: ${sl:,.8f}\n"
                    f"🎯 Take-profit: ${tp:,.8f}"
                )
            
            await update.message.reply_text(respuesta, parse_mode="Markdown")
            
        except Exception as e:
            logging.error(f"Error en estrategia: {str(e)}", exc_info=True)
            await update.message.reply_text("⚠️ Error en el análisis")

    def health_check(self):
        """Mantiene activo el servicio en Render"""
        try:
            if os.getenv('RENDER'):
                requests.get(os.getenv('WEBHOOK_URL'), timeout=5)
                self.health_check_active = True
        except Exception as e:
            logging.warning(f"Health check failed: {e}")
            self.health_check_active = False
        finally:
            threading.Timer(HEALTH_CHECK_MIN * 60, self.health_check).start()

def main():
    # Validación de seguridad
    if not token:
        logging.critical("Token no configurado. Verifica TOKEN_BOT")
        return

    # Inicializar bot
    bot = ShibTradingBot()
    app = Application.builder().token(token).build()
    
    # Registrar comandos
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("precio", bot.precio_shib))
    app.add_handler(CommandHandler("estrategia", bot.estrategia_trading))
    app.add_handler(CommandHandler("ayuda", bot.start))  # Alias para /start
    
    # Iniciar health check
    if os.getenv('RENDER'):
        bot.health_check()
        logging.info("Modo webhook activado")
        app.run_webhook(
            listen="0.0.0.0",
            port=10000,
            webhook_url=os.getenv('WEBHOOK_URL'),
            secret_token=os.getenv('SECRET_TOKEN'),
            drop_pending_updates=True
        )
    else:
        logging.info("Modo polling activado")
        app.run_polling(
            poll_interval=2,
            timeout=15,
            drop_pending_updates=True
        )

if __name__ == "__main__":
    main()
