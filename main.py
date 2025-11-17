import logging
import os

from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


def load_questions() -> list[dict[str, str]]:
    questions = []
    answers = []
    for number in range(1198, 1202):
        with open(f"questions_archive/1vs{number}.txt", encoding="koi8-r") as file:
            text = file.read()

        parts = text.split("\n\n")
        for part in parts:
            part = part.strip()
            if part.startswith("Вопрос"):
                questions.append(
                    part.split(":", 1)[-1].replace("\n", " ").strip()
                )
            if part.startswith("Ответ"):
                answers.append(
                    part.split(":", 1)[-1].replace("\n", " ").strip()
                )
    return [{"question": q, "answer": a} for q, a in zip(questions, answers)]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(text=rf"Hi, {user.mention_html()}!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(text=update.message.text)


def main():
    questions = load_questions()

    token = os.getenv("TELEGRAM_TOKEN")
    application = Application.builder().token(token=token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    main()
