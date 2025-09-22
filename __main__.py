import os
import random
import json
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Application, InlineQueryHandler, ContextTypes, CommandHandler
from uuid import uuid4
from dotenv import load_dotenv
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

load_dotenv()

DATA_FILE = "quotes.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {
            "quotes": [
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
            ],
            "suggestions": []
        }

DATA = load_data()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

def get_random_quote():
    return random.choice(DATA["quotes"])

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

async def suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите цитату для предложения.")
        return
    quote = " ".join(context.args).strip()
    DATA["suggestions"].append({"user_id": user.id, "quote": quote})
    save_data(DATA)
    await update.message.reply_text("Спасибо за предложение! Ваша цитата отправлена на рассмотрение.")

async def addquote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для добавления цитат.")
        return
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите цитату для добавления.")
        return
    quote = " ".join(context.args).strip()
    DATA["quotes"].append(quote)
    save_data(DATA)
    await update.message.reply_text("Цитата успешно добавлена.")

async def listsuggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для просмотра предложений.")
        return
    if not DATA["suggestions"]:
        await update.message.reply_text("Нет предложенных цитат.")
        return
    messages = []
    for i, item in enumerate(DATA["suggestions"], start=1):
        messages.append(f"{i}. {item['quote']} (от пользователя {item['user_id']})")
    await update.message.reply_text("\n".join(messages))

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для одобрения цитат.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Пожалуйста, укажите номер цитаты для одобрения.")
        return
    index = int(context.args[0]) - 1
    if index < 0 or index >= len(DATA["suggestions"]):
        await update.message.reply_text("Неверный номер цитаты.")
        return
    quote = DATA["suggestions"].pop(index)["quote"]
    DATA["quotes"].append(quote)
    save_data(DATA)
    await update.message.reply_text("Цитата одобрена и добавлена в основной список.")

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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
    application.add_handler(CommandHandler("suggest", suggest))
    application.add_handler(CommandHandler("addquote", addquote))
    application.add_handler(CommandHandler("listsuggest", listsuggest))
    application.add_handler(CommandHandler("approve", approve))

    print("Бот запущен. Нажми Ctrl+C для выхода.")
    application.run_polling()

if __name__ == '__main__':
    threading.Thread(target=run_http_server, daemon=True).start()
    main()