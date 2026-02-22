import os
import random
import json
from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    InlineQueryHandler,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from uuid import uuid4
from dotenv import load_dotenv
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

load_dotenv()

DATA_FILE = "/data/quotes.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        data = {
            "quotes": [
                "Вълкъ слабее льва и тигра, но в цирке не выступает",
                "Вълкъ - не тот, кто wolf, а тот, кто Canis lupus",
                "Если вълкъ и работает в цирке, то только начальником",
                "Если вълкъ голодный, лучше его покормить",
                "Если запутался, распутайся",
                "Чтобы не искать выход, посмотри внимательно на вход.",
                "Каждый может кинуть камень в вълка, но не каждый может кинуть вълка в камень",
                "Робота - не волк. Работа - это ворк, а волк - это ходить",
                "Не тот вълкъ кто не вълкъ а вълкъ тот кто вълкъ но не каждый вълкъ настоящий вълкъ а только настоящий вълкъ вълкъ",
                "Припапупапри",
                "Не стоит искать вълка там, где его нет, - его там нет",
                "Друг наполовину - это всегда наполовину друг",
                "Если дофига умный - умничай, но помни: без ума умничать не выйдет. Так что будь умным, чтобы умничать",
                "В этой жизни ты либо вълкъ, либо не вълкъ",
                "Что бессмысленно, то не имеет смысла"
            ],
            "suggestions": []
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return data

DATA = load_data()

ADMIN_ID = int(os.getenv("ADMIN_ID"))

def get_random_quote():
    return random.choice(DATA["quotes"])

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()

    quote_text = None
    title = "Вспомнить мудрость"

    # если пользователь ввёл число — считаем, что это номер цитаты
    if query.isdigit():
        index = int(query) - 1
        if 0 <= index < len(DATA["quotes"]):
            quote_text = DATA["quotes"][index]
            title = f"Мудрость №{query}"
        else:
            quote_text = "❌ Цитаты с таким номером не существует."
            title = "Ошибка"
    else:
        quote_text = get_random_quote()

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=title,
            input_message_content=InputTextMessageContent(
                f"{quote_text}"
            ),
            description=quote_text[:80]
        )
    ]

    await update.inline_query.answer(results, cache_time=0, is_personal=True)

async def suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "suggest"
    await update.message.reply_text("✍️ Введите цитату для предложения.")

async def addquote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для добавления цитат")
        return

    context.user_data["mode"] = "add"
    await update.message.reply_text("🐺 Введите цитату для добавления.")

async def listsuggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для просмотра предложений")
        return
    if not DATA["suggestions"]:
        await update.message.reply_text("Нет предложенных цитат")
        return
    messages = []
    for i, item in enumerate(DATA["suggestions"], start=1):
        messages.append(f"{i}. {item['quote']} (от пользователя {item['user_id']})")
    await update.message.reply_text("\n".join(messages))

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для одобрения цитат")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Пожалуйста, укажите номер цитаты для одобрения")
        return
    index = int(context.args[0]) - 1
    if index < 0 or index >= len(DATA["suggestions"]):
        await update.message.reply_text("Неверный номер цитаты")
        return
    quote = DATA["suggestions"].pop(index)["quote"]
    DATA["quotes"].append(quote)
    save_data(DATA)
    await update.message.reply_text("Цитата одобрена и добавлена в основной список")

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для отклонения цитат")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Пожалуйста, укажите номер цитаты для отклонения")
        return
    index = int(context.args[0]) - 1
    if index < 0 or index >= len(DATA["suggestions"]):
        await update.message.reply_text("Неверный номер цитаты")
        return
    quote = DATA["suggestions"].pop(index)["quote"]
    await update.message.reply_text("Цитата оказалась слишком говном")

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "mode" not in context.user_data:
        return

    text = update.message.text.strip()
    context.user_data["pending_quote"] = text

    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"),
            InlineKeyboardButton("❌ Отменить", callback_data="cancel")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Вот что вы ввели:\n\n{text}\n\nПодтвердить?",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if "pending_quote" not in context.user_data:
        await query.edit_message_text("⚠️ Данные устарели.")
        return

    quote = context.user_data["pending_quote"]
    mode = context.user_data.get("mode")

    if query.data == "confirm":
        if mode == "suggest":
            DATA["suggestions"].append({
                "user_id": update.effective_user.id,
                "quote": quote
            })
            save_data(DATA)
            await query.edit_message_text("✅ Цитата отправлена на рассмотрение.")

        elif mode == "add":
            DATA["quotes"].append(quote)
            save_data(DATA)
            await query.edit_message_text("🔥 Цитата добавлена.")

    elif query.data == "cancel":
        await query.edit_message_text("❌ Действие отменено.")

    context.user_data.clear()

async def start_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        'Добро пожаловать в бот Вълчьи цитаты"! Этот бот создан @TheSameFail\n\n'
        "Здесь вы можете предложить свою цитату. Ниже будут приведены все доступные команды\n\n"
        "Список команд:\n\n"
        "/suggest - предложить новую цитату\n"
        "/help - показать список команд\n"
        "/start - старт бота\n"
    )
    await update.message.reply_text(text)

async def show_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_ID:
        commands_text = (
            '📜 Общие команды:\n\n'
            "/suggest <цитата> - предложить новую цитату\n"
            "/help - показать список команд\n"
            "/start - приветствие и список команд\n\n"
            "Админские команды:\n\n"
            "/addquote <цитата> - добавить цитату\n"
            "/listsuggest - показать предложения цитат\n"
            "/approve <номер> - одобрить предложение и добавить в основной список\n"
            "/reject - отклонить цитату"
        )
    else:
        commands_text = (
            '📜 Список команд бота "Вълчьи цитаты":\n\n'
            "/suggest - предложить новую цитату\n"
            "/help - показать список команд\n"
            "/start - старт бота\n"
        )
    await update.message.reply_text(commands_text)

async def post_init(application):
    from telegram import BotCommand, BotCommandScopeDefault, BotCommandScopeChat

    # Команды для всех
    public_commands = [
        BotCommand("suggest", "Предложить новую цитату"),
        BotCommand("help", "Список всех команд"),
        BotCommand("start", "Старт бота"),
    ]

    # Команды только для админа
    admin_commands = [
        BotCommand("addquote", "Добавить цитату"),
        BotCommand("listsuggest", "Показать предложения"),
        BotCommand("approve", "Одобрить цитату"),
        BotCommand("reject", "Отклонить цитату"),
    ]

    await application.bot.set_my_commands(
        public_commands,
        scope=BotCommandScopeDefault()
    )

    # Устанавливаем админские команды только для тебя
    await application.bot.set_my_commands(
        public_commands + admin_commands,
        scope=BotCommandScopeChat(chat_id=ADMIN_ID)
    )

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

    application = Application.builder().token(token).post_init(post_init).build()

    application.add_handler(InlineQueryHandler(inline_query_handler))
    application.add_handler(CommandHandler("suggest", suggest))
    application.add_handler(CommandHandler("addquote", addquote))
    application.add_handler(CommandHandler("listsuggest", listsuggest))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("help", show_commands))
    application.add_handler(CommandHandler("start", start_message))
    application.add_handler(CommandHandler("reject", reject))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен. Нажми Ctrl+C для выхода.")
    application.run_polling()

if __name__ == '__main__':
    threading.Thread(target=run_http_server, daemon=True).start()
    main()