# telegram-messager.py
import os, asyncio, random, logging
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from aiohttp import web

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

API_ID = int(os.getenv("API_ID", "2040"))
API_HASH = os.getenv("API_HASH", "b18441a1ff607e10a989891a5462e627")
SESSION_STRING = os.getenv("SESSION_STRING", "")
TARGET = os.getenv("TARGET", "")   # e.g. -1001234567890
INTERVAL = int(os.getenv("INTERVAL", "240"))  # 3 دقیقه = 180 ثانیه
MESSAGES = os.getenv("MESSAGES").split("؛")
JITTER = int(os.getenv("JITTER", "0"))  # می‌تونی صفر بذاری برای دقیق بودن
PORT = int(os.getenv("PORT", "3000"))

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH, connection_retries=5)

async def send_loop():
    await client.start()
    logging.info("Telegram client started.")
    while True:
        start_time = asyncio.get_event_loop().time()  # زمان شروع پیام
        try:
            msg = random.choice(MESSAGES).strip() or "سلام"
            jitter = random.randint(-JITTER, JITTER) if JITTER > 0 else 0
            logging.info(f"Sending to {TARGET}: {msg}")
            await client.send_message(int(TARGET), msg)

            # محاسبه زمان باقی‌مانده تا INTERVAL بعدی
            elapsed = asyncio.get_event_loop().time() - start_time
            wait = max(0, INTERVAL + jitter - elapsed)
            logging.info(f"Next message in {wait:.1f}s")
            await asyncio.sleep(wait)

        except errors.FloodWaitError as e:
            logging.warning(f"FloodWait {e.seconds}s — sleeping")
            await asyncio.sleep(e.seconds + 5)
        except Exception as e:
            logging.exception("Error sending — retrying after short delay")
            await asyncio.sleep(30)

async def keep_alive():
    app = web.Application()
    async def handle(req): return web.Response(text="ok")
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"Keep-alive server on port {PORT}")

async def main():
    await keep_alive()
    await send_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Stopped")
