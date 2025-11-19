import re
from pathlib import Path


def _extract_text(text: str) -> str:
    return text.split(":", 1)[-1].replace("\n", " ").strip()


def load_questions() -> dict[str, str]:
    archive_path = Path("questions_archive")
    if not archive_path.exists():
        print(f"Папка {archive_path} не найдена.")
        return {}

    questions = []
    answers = []
    txt_files = archive_path.glob("*.txt")
    for file_path in txt_files:
        try:
            with open(file_path, encoding="koi8-r") as file:
                text = file.read()

            parts = text.split("\n\n")
            for part in parts:
                part = part.strip()
                if part.startswith("Вопрос"):
                    questions.append(_extract_text(part))
                if part.startswith("Ответ"):
                    answers.append(_extract_text(part))
        except Exception as exc:
            print(f"Ошибка чтения файла {file_path}: {str(exc)}")
            continue

    return {q: a for q, a in zip(questions, answers)}


def is_answer_correct(user_answer: str, correct_answer: str) -> bool:
    parts = re.split(r"[.(]", correct_answer, 1)
    return user_answer.strip().lower() == parts[0].strip().lower()
