import logging
import random
from enum import Enum, auto

import vk_api as vk
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType, Event
from vk_api.vk_api import VkApiMethod

from config import Config
from quiz import load_questions, is_answer_correct
from redis_client import redis


class State(int, Enum):
    ANSWER = auto()


user_states = {}


def vk_user_id(user_id: int) -> str:
    return f"vk_{user_id}"


def create_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


reply_keyboard = create_keyboard()
quiz = load_questions()


def random_question() -> str:
    return random.choice(list(quiz.keys()))


def send_message(vk_api: VkApiMethod, user_id: int, message: str, keyboard: str | None = None) -> None:
    random_id = random.randint(1, 1_000_000)
    vk_api.messages.send(
        user_id=user_id,
        message=message,
        keyboard=keyboard,
        random_id=random_id,
    )


def handle_new_question_request(vk_api: VkApiMethod, user_id: int) -> None:
    question = random_question()
    redis.set(vk_user_id(user_id), question)
    user_states[user_id] = State.ANSWER
    send_message(vk_api, user_id, question, reply_keyboard)


def handle_solution_attempt(vk_api: VkApiMethod, user_id: int, user_answer: str) -> None:
    question = redis.get(vk_user_id(user_id))
    if not question:
        send_message(
            vk_api,
            user_id,
            "Сначала нажмите 'Новый вопрос'",
            reply_keyboard,
        )
        user_states[user_id] = None
        return

    if is_answer_correct(user_answer=user_answer, correct_answer=quiz.get(question)):
        send_message(
            vk_api,
            user_id,
            "Правильно! Поздравляю! Для следующего вопроса нажмите 'Новый вопрос'",
            reply_keyboard,
        )
        user_states[user_id] = None
    else:
        send_message(
            vk_api,
            user_id,
            "Неправильно… Попробуешь ещё раз?",
            reply_keyboard,
        )
        user_states[user_id] = State.ANSWER


def handle_give_up(vk_api: VkApiMethod, user_id: int) -> None:
    question = redis.get(vk_user_id(user_id))

    if not question:
        send_message(
            vk_api,
            user_id,
            "Сначала нажмите 'Новый вопрос'",
            reply_keyboard,
        )
        user_states[user_id] = None
        return

    correct_answer = quiz.get(question)
    send_message(
        vk_api,
        user_id,
        f"Правильный ответ: {correct_answer}",
        reply_keyboard,
    )

    new_question = random_question()
    redis.set(vk_user_id(user_id), new_question)
    send_message(
        vk_api,
        user_id,
        f"Следующий вопрос: {new_question}",
        reply_keyboard,
    )
    user_states[user_id] = State.ANSWER


def process_events(event: Event, vk_api: VkApiMethod) -> None:
    user_id = event.user_id
    text = event.text.strip()

    current_state = user_states.get(user_id)

    if text == "Новый вопрос":
        handle_new_question_request(vk_api, user_id)
    elif text == "Сдаться":
        if current_state == State.ANSWER:
            handle_give_up(vk_api, user_id)
        else:
            send_message(
                vk_api,
                user_id,
                "Нажмите 'Новый вопрос' чтобы начать викторину!",
                keyboard=reply_keyboard,
            )
    elif current_state == State.ANSWER:
        handle_solution_attempt(vk_api, user_id, text)
    else:
        send_message(
            vk_api,
            user_id,
            "Нажмите 'Новый вопрос' чтобы начать викторину!",
            reply_keyboard,
        )


def main():
    vk_session = vk.VkApi(token=Config.VK_TOKEN)
    vk_api = vk_session.get_api()
    long_poll = VkLongPoll(vk_session)
    for event in long_poll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            process_events(event, vk_api)


if __name__ == "__main__":
    try:
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
        main()
    except KeyboardInterrupt:
        print("Завершение работы")
