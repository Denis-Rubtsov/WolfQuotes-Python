import os
import random
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Application, InlineQueryHandler, ContextTypes
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

QUOTES = [
    "Вълкъ слабее льва и тигра, но в цирке не выступает",
    "Вълкъ - не тот, кто волк, а тот, кто Canis lupus",
    "Если вълкъ и работает в цирке, то только начальником",
    "Если вълкъ голодный, лучше его покормить",
    "Если запутался, распутайся",
    "Чтобы не искать выход, посмотри внимательно на вход.",
    "Каждый может кинуть камень в вълка, но не каждый может кинуть вълка в камень",
    "Робота - не волк. Работа - это ворк, а волк - это ходить"
]

def get_random_quote():
    return random.choice(QUOTES)

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Вспомнить мудрость",
            input_message_content=InputTextMessageContent(get_random_quote()),
            description="Вы вспоминаете мудрость Великого вълка"
        )
    ]

    await update.inline_query.answer(results, cache_time=0, is_personal=True)

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")  # Задай токен в переменной среды или .env
    if not token:
        print("Не найден TELEGRAM_BOT_TOKEN в переменных среды")
        return

    application = Application.builder().token(token).build()

    application.add_handler(InlineQueryHandler(inline_query_handler))

    print("Бот запущен. Нажми Ctrl+C для выхода.")
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())