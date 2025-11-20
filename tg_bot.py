import logging
import os
import random
from enum import Enum, auto

from dotenv import load_dotenv
from redis import Redis
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from quiz import load_questions, is_answer_correct
from redis_client import connect_redis

redis: Redis | None = None


class State(int, Enum):
    ANSWER = auto()


def _create_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("Новый вопрос"),
                KeyboardButton("Сдаться"),
            ],
            [
                KeyboardButton("Мой счёт"),
            ],
        ],
        resize_keyboard=True,
    )


reply_keyboard = _create_keyboard()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(
        text="Привет! Я бот для викторин!",
        reply_markup=reply_keyboard,
    )


async def handle_new_question_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    quiz: dict[str, str] = context.bot_data["quiz"]
    user_id = f"telegram_{update.effective_user.id}"
    question = random.choice(list(quiz.keys()))
    redis.set(user_id, question)
    await update.message.reply_text(text=question, reply_markup=reply_keyboard)
    return State.ANSWER


async def handle_solution_attempt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    quiz: dict[str, str] = context.bot_data["quiz"]
    user_id = f"telegram_{update.effective_user.id}"
    user_answer = update.message.text.strip()

    question = redis.get(user_id)

    if not question:
        await update.message.reply_text("Сначала нажмите 'Новый вопрос'", reply_markup=reply_keyboard)
        return ConversationHandler.END

    if is_answer_correct(user_answer=user_answer, correct_answer=quiz.get(question)):
        await update.message.reply_text(
            text="Правильно! Поздравляю! Для следующего вопроса нажмите 'Новый вопрос'",
            reply_markup=reply_keyboard
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(text="Неправильно… Попробуешь ещё раз?", reply_markup=reply_keyboard)
        return State.ANSWER


async def give_up_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    quiz: dict[str, str] = context.bot_data["quiz"]
    user_id = f"telegram_{update.effective_user.id}"

    question = redis.get(user_id)

    if not question:
        await update.message.reply_text(text="Сначала нажмите 'Новый вопрос'", reply_markup=reply_keyboard)
        return ConversationHandler.END

    correct_answer = quiz.get(question)
    await update.message.reply_text(text=f"Правильный ответ: {correct_answer}", reply_markup=reply_keyboard)

    new_question = random.choice(list(quiz.keys()))
    redis.set(user_id, new_question)
    await update.message.reply_text(text=f"Следующий вопрос: {new_question}", reply_markup=reply_keyboard)
    return State.ANSWER


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(text="Диалог завершен", reply_markup=reply_keyboard)
    return ConversationHandler.END


def main():
    global redis

    load_dotenv()
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    host = os.environ["REDIS_HOST"]
    port = int(os.environ["REDIS_PORT"])
    username = os.environ["REDIS_USERNAME"]
    password = os.environ["REDIS_PASSWORD"]
    redis = connect_redis(host, port, username, password)
    token = os.environ["TELEGRAM_TOKEN"]
    application = Application.builder().token(token=token).build()
    application.bot_data["quiz"] = load_questions()

    conversation_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Новый вопрос$"), handle_new_question_request)],
        states={
            State.ANSWER: [
                MessageHandler(filters.Regex("^Сдаться$"), give_up_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_solution_attempt),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        allow_reentry=True,
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conversation_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
