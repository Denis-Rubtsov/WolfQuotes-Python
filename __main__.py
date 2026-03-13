import os
import random
import json

from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultVoice,
    InlineQueryResultsButton
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

load_dotenv()
BASIC_URL = os.getenv("BASIC_URL")

DATA_FILE = "/data/quotes.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else: return None

DATA = load_data()

ADMIN_ID = int(os.getenv("ADMIN_ID"))

def get_random_quote():
    return random.choice(DATA["quotes"])

def quote_exists(new_quote: str) -> bool:
    normalized = new_quote.strip().lower()
    return any(
        q.strip().lower() == normalized
        for q in DATA["quotes"]
    )

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    title = "Вспомнить мудрость"
    quote_text = None
    voice_url = None

    if query.isdigit():
        index = int(query) - 1
        if 0 <= index < len(DATA["quotes"]):
            quote_text = DATA["quotes"][index]
            title = f"Мудрость №{query}"
            quote_number = query
        else:
            results = []
            await update.inline_query.answer(
                results,
                cache_time=0,
                is_personal=True,
                button=InlineQueryResultsButton(
                    text=f"Введите номер цитаты (от 1 до {quote_list_lenght})",
                    start_parameter="start"
                )
            )
    else:
        quote_text = get_random_quote()
        quote_number = DATA["quotes"].index(quote_text) + 1

    voice_url = BASIC_URL + f"{quote_number}.ogg"

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=title,
            input_message_content=InputTextMessageContent(
                f"{quote_text}"
            ),
            description=quote_text[:80]
        ),
        InlineQueryResultVoice(
            id=str(uuid4()),
            title=title + " голосом Волка",
            voice_url=voice_url,
        )
    ]
    quote_list_lenght = len(DATA["quotes"])
    await update.inline_query.answer(
        results,
        cache_time=0,
        is_personal=True,
        button=InlineQueryResultsButton(
            text=f"Введите номер цитаты (от 1 до {quote_list_lenght})",
            start_parameter="start"
        )
    )

async def suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "suggest"
    await update.message.reply_text("✍️ Введите цитату для предложения.")

def check_user(user):
    if user.id != ADMIN_ID:
        print("У вас нет прав на эту команду")
        return False
    return True

async def add_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_user(update.effective_user):
        return

    context.user_data["mode"] = "add"
    await update.message.reply_text("🐺 Введите цитату для добавления.")

async def list_suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_user(user):
        return
    if not DATA["suggestions"]:
        await update.message.reply_text("Нет предложенных цитат")
        return
    messages = []
    for i, item in enumerate(DATA["suggestions"], start=1):
        messages.append(f"{i}. {item['quote']} (от пользователя {item['user_id']})")
    await update.message.reply_text("\n".join(messages))

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_user(update.effective_user):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Пожалуйста, укажите номер цитаты для одобрения")
        return
    index = int(context.args[0]) - 1
    if index < 0 or index >= len(DATA["suggestions"]):
        await update.message.reply_text("Неверный номер цитаты")
        return
    quote = DATA["suggestions"][index]["quote"]
    if not quote_exists(quote):
        quote = DATA["suggestions"].pop(index)["quote"]
        DATA["quotes"].append(quote)
        save_data(DATA)
        await update.message.reply_text("Цитата одобрена и добавлена в основной список")
    else:
        await update.message.reply_text("⚠️ Такая цитата уже существует.")

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
    save_data(DATA)
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

async def alert(context: ContextTypes.DEFAULT_TYPE, quote: str, tag: str, index: int):
    keyboard = [
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"admin_approve:{index}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_reject:{index}")
        ]
    ]
    text = f"Новое предложение от {tag}: " + quote
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    action, index = query.data.split(":")
    index = int(index)

    if index < 0 or index >= len(DATA["suggestions"]):
        await query.edit_message_text("⚠️ Предложение устарело.")
        return

    item = DATA["suggestions"][index]
    quote = item["quote"]
    user_id = item["user_id"]

    if action == "admin_approve":
        if not quote_exists(quote):
            DATA["quotes"].append(quote)
            DATA["suggestions"].pop(index)
            save_data(DATA)

            await context.bot.send_message(
                chat_id=user_id,
                text="🐺 Ваша цитата была одобрена!"
            )

            await query.edit_message_text("✅ Цитата одобрена.")
        else:
            await query.edit_message_text("⚠️ Такая цитата уже существует.")

    elif action == "admin_reject":
        DATA["suggestions"].pop(index)
        save_data(DATA)

        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Ваша цитата была отклонена."
        )

        await query.edit_message_text("Цитата отклонена.")


async def handle_user_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if "pending_quote" not in context.user_data:
        await query.edit_message_text("⚠️ Данные устарели.")
        return

    quote = context.user_data["pending_quote"]
    mode = context.user_data.get("mode")

    if query.data == "confirm":
        if mode == "suggest":
            tag = f"@{update.effective_user.username}" if update.effective_user.username else update.effective_user.first_name

            DATA["suggestions"].append({
                "user_id": update.effective_user.id,
                "name": tag,
                "quote": quote
            })
            save_data(DATA)

            index = len(DATA["suggestions"]) - 1
            await alert(context, quote, tag, index)

            await query.edit_message_text("✅ Цитата отправлена на рассмотрение.")

        elif mode == "add":
            if not quote_exists(quote):
                DATA["quotes"].append(quote)
                save_data(DATA)
                await query.edit_message_text("🔥 Цитата добавлена.")
            else:
                await query.edit_message_text("⚠️ Такая цитата уже существует.")

    elif query.data == "cancel":
        await query.edit_message_text("❌ Действие отменено.")

    context.user_data.clear()

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("admin_"):
        if update.effective_user.id != ADMIN_ID:
            await query.edit_message_text("❌ Нет прав.")
            return
        await handle_admin_buttons(update, context)
        return

    await handle_user_confirmation(update, context)

COMMAND_LIST = (
        '📜 Список команд бота "Вълчьи цитаты":\n\n'
        "/suggest - предложить новую цитату\n"
        "/help - показать список команд\n"
        "/start - старт бота\n"
        "/list - показать все цитаты"
        )

async def start_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        'Добро пожаловать в бот "Вълчьи цитаты"! Этот бот создан @TheSameFail\n\n'
        "Здесь вы можете предложить свою цитату. Ниже будут приведены все доступные команды\n\n"
    ) + COMMAND_LIST
    await update.message.reply_text(text)

async def all_quotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ""
    quotes = DATA["quotes"]
    for i in range(len(quotes)):
        text += f"{i +1}. {quotes[i]} \n"
    await update.message.reply_text(text)

async def show_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_ID:
        commands_text = COMMAND_LIST + (
            "Админские команды:\n\n"
            "/addquote <цитата> - добавить цитату\n"
            "/listsuggest - показать предложения цитат\n"
            "/approve <номер> - одобрить предложение и добавить в основной список\n"
            "/reject <номер> - отклонить цитату"
        )
    else:
        commands_text = COMMAND_LIST
    await update.message.reply_text(commands_text)

async def post_init(application):
    from telegram import BotCommand, BotCommandScopeDefault, BotCommandScopeChat

    public_commands = [
        BotCommand("suggest", "Предложить новую цитату"),
        BotCommand("help", "Список всех команд"),
        BotCommand("start", "Старт бота"),
        BotCommand("list", "Показать все цитаты"),
    ]

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

    await application.bot.set_my_commands(
        public_commands + admin_commands,
        scope=BotCommandScopeChat(chat_id=ADMIN_ID)
    )

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")  # Задай токен в переменной среды или .env
    if not token:
        print("Не найден TELEGRAM_BOT_TOKEN в переменных среды")
        return

    application = Application.builder().token(token).post_init(post_init).build()
    application.add_handler(InlineQueryHandler(inline_query_handler))
    application.add_handler(CommandHandler("suggest", suggest))
    application.add_handler(CommandHandler("addquote", add_quote))
    application.add_handler(CommandHandler("listsuggest", list_suggest))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("help", show_commands))
    application.add_handler(CommandHandler("start", start_message))
    application.add_handler(CommandHandler("reject", reject))
    application.add_handler(CommandHandler("list", all_quotes))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен. Нажми Ctrl+C для выхода.")
    application.run_polling()

if __name__ == '__main__':
    main()