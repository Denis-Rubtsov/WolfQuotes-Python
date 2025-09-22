import os
import random
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Application, InlineQueryHandler, ContextTypes
from uuid import uuid4
from dotenv import load_dotenv
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

load_dotenv()

QUOTES = [
    "Вълкъ слабее льва и тигра, но в цирке не выступает",
        "Вълкъ - не тот, кто wolf, а тот, кто Canis lupus",
        "Если вълкъ и работает в цирке, то только начальником",
        "Если вълкъ голодный, лучше его покормить",
        "Если запутался, распутайся",
        "Чтобы не искать выход, посмотри внимательно на вход.",
        "Каждый может кинуть камень в вълка, но не каждый может кинуть вълка в камень",
        "Робота - не волк. Работа - это ворк, а волк - это ходить",
        "Не тот волк кто не волк а волк тот кто волк но не каждый волк настоящий волк а только настоящий волк волк",
        "Припапупапри",
        "Не стоит искать вълка там, где его нет, - его там нет",
        "Друг наполовину - это всегда наполовину друг",
        "Если дофига умный - умничай, но помни: без ума умничать не выйдет. Так что будь умным, чтобы умничать",
        "В этой жизни ты либо вълкъ, либо не вълкъ",
        "Что бессмысленно, то не имеет смысла"
]

def get_random_quote():
    return random.choice(QUOTES)

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Вспомнить мудрость",
            input_message_content=InputTextMessageContent(f"{get_random_quote()}\n\nМудростью поделился Великий Вълкъ - @Vlk_quote_bot"),
            description="Вы вспоминаете мудрость Великого вълка"
        )
    ]

    await update.inline_query.answer(results, cache_time=0, is_personal=True)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_http_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"HTTP healthcheck server запущен на порту {port}")
    server.serve_forever()

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")  # Задай токен в переменной среды или .env
    if not token:
        print("Не найден TELEGRAM_BOT_TOKEN в переменных среды")
        return

    application = Application.builder().token(token).build()

    application.add_handler(InlineQueryHandler(inline_query_handler))

    print("Бот запущен. Нажми Ctrl+C для выхода.")
    application.run_polling()

if __name__ == '__main__':
    threading.Thread(target=run_http_server, daemon=True).start()
    main()