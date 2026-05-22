import asyncio
import json
import random
from datetime import date, datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove

from telegram_bots.config import bot_token
from telegram_bots.services import closest_product, translate_text
from telegram_bots.services import yandex_geocode, yandex_static_map_url


def create_echo_bot():
    dp = Dispatcher()

    @dp.message(F.text)
    async def echo(message):
        await message.answer(f"Я получил сообщение {message.text}")

    return Bot(bot_token()), dp


def create_time_date_bot():
    dp = Dispatcher()

    @dp.message(Command("time"))
    async def send_time(message):
        await message.answer(datetime.now().strftime("%H:%M:%S"))

    @dp.message(Command("date"))
    async def send_date(message):
        await message.answer(date.today().strftime("%d.%m.%Y"))

    return Bot(bot_token()), dp


def create_board_game_bot():
    dp = Dispatcher()
    timers = {}

    main_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/dice"), KeyboardButton(text="/timer")]
        ],
        resize_keyboard=True,
    )
    dice_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="кинуть один шестигранный кубик")],
            [
                KeyboardButton(
                    text="кинуть 2 шестигранных кубика одновременно"
                )
            ],
            [KeyboardButton(text="кинуть 20-гранный кубик")],
            [KeyboardButton(text="вернуться назад")],
        ],
        resize_keyboard=True,
    )
    timer_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="30 секунд"),
                KeyboardButton(text="1 минута"),
            ],
            [
                KeyboardButton(text="5 минут"),
                KeyboardButton(text="вернуться назад"),
            ],
        ],
        resize_keyboard=True,
    )
    close_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="/close")]],
        resize_keyboard=True,
    )

    async def finish_timer(chat_id, text, bot):
        try:
            seconds = {
                "30 секунд": 30,
                "1 минута": 60,
                "5 минут": 300,
            }[text]
            await asyncio.sleep(seconds)
            await bot.send_message(
                chat_id,
                f"{text} истекло",
                reply_markup=timer_keyboard,
            )
        finally:
            timers.pop(chat_id, None)

    @dp.message(Command("start"))
    async def start(message):
        await message.answer("Выберите режим.", reply_markup=main_keyboard)

    @dp.message(Command("dice"))
    async def dice(message):
        await message.answer("Выберите кубик.", reply_markup=dice_keyboard)

    @dp.message(Command("timer"))
    async def timer(message):
        await message.answer("Выберите время.", reply_markup=timer_keyboard)

    @dp.message(Command("close"))
    async def close(message):
        task = timers.pop(message.chat.id, None)
        if task:
            task.cancel()
        await message.answer("Таймер сброшен.", reply_markup=main_keyboard)

    @dp.message(F.text == "вернуться назад")
    async def back(message):
        await message.answer("Главное меню.", reply_markup=main_keyboard)

    dice_buttons = {
        "кинуть один шестигранный кубик",
        "кинуть 2 шестигранных кубика одновременно",
        "кинуть 20-гранный кубик",
    }

    @dp.message(F.text.in_(dice_buttons))
    async def roll(message):
        if message.text == "кинуть один шестигранный кубик":
            result = str(random.randint(1, 6))
        elif message.text == "кинуть 2 шестигранных кубика одновременно":
            result = f"{random.randint(1, 6)} {random.randint(1, 6)}"
        else:
            result = str(random.randint(1, 20))
        await message.answer(result, reply_markup=dice_keyboard)

    @dp.message(F.text.in_({"30 секунд", "1 минута", "5 минут"}))
    async def set_timer(message, bot):
        old_task = timers.pop(message.chat.id, None)
        if old_task:
            old_task.cancel()
        timers[message.chat.id] = asyncio.create_task(
            finish_timer(message.chat.id, message.text, bot)
        )
        await message.answer(
            f"засек {message.text}",
            reply_markup=close_keyboard,
        )

    return Bot(bot_token()), dp


MUSEUM_GRAPH = {
    "entrance": {
        "text": (
            "Добро пожаловать! "
            "Пожалуйста, сдайте верхнюю одежду в гардероб!"
        ),
        "next": {"Зал 1": "Античная коллекция"},
    },
    "Зал 1": {
        "text": "В данном зале представлено античное искусство.",
        "next": {"Зал 2": "Живопись", "Зал 3": "Скульптура"},
    },
    "Зал 2": {
        "text": "В данном зале представлена европейская живопись.",
        "next": {"Зал 4": "Современное искусство"},
    },
    "Зал 3": {
        "text": "В данном зале представлена скульптура.",
        "next": {"Зал 4": "Современное искусство"},
    },
    "Зал 4": {
        "text": "В данном зале представлено современное искусство.",
        "next": {"exit": "Выход из музея"},
    },
    "exit": {
        "text": (
            "Всего доброго, не забудьте забрать верхнюю одежду "
            "в гардеробе!"
        ),
        "next": {},
    },
}


def museum_state_diagram():
    state_ids = {
        "entrance": "entrance",
        "Зал 1": "room1",
        "Зал 2": "room2",
        "Зал 3": "room3",
        "Зал 4": "room4",
        "exit": "museum_exit",
    }
    lines = [
        "stateDiagram-v2",
        '    state "Вход" as entrance',
        '    state "Зал 1" as room1',
        '    state "Зал 2" as room2',
        '    state "Зал 3" as room3',
        '    state "Зал 4" as room4',
        '    state "Выход" as museum_exit',
        "    [*] --> entrance",
    ]
    for room, data in MUSEUM_GRAPH.items():
        for target in data["next"]:
            lines.append(f"    {state_ids[room]} --> {state_ids[target]}")
    lines.append("    museum_exit --> [*]")
    return "\n".join(lines)


def create_museum_bot():
    dp = Dispatcher()
    user_rooms = {}

    def keyboard_for(room):
        if not MUSEUM_GRAPH[room]["next"]:
            return ReplyKeyboardRemove()
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=name)]
                for name in MUSEUM_GRAPH[room]["next"]
            ],
            resize_keyboard=True,
        )

    async def show_room(message, room):
        user_rooms[message.chat.id] = room
        data = MUSEUM_GRAPH[room]
        choices = "\n".join(
            f"{name}: {description}"
            for name, description in data["next"].items()
        )
        if choices:
            suffix = f"\n\nМожно перейти:\n{choices}"
        else:
            suffix = "\n\nЭкскурсия завершена."
        await message.answer(
            f"{data['text']}{suffix}",
            reply_markup=keyboard_for(room),
        )

    @dp.message(Command("start"))
    async def start(message):
        await show_room(message, "entrance")

    @dp.message(F.text)
    async def move(message):
        current = user_rooms.get(message.chat.id, "entrance")
        if message.text in MUSEUM_GRAPH[current]["next"]:
            await show_room(message, message.text)
        else:
            await message.answer(
                "Такого перехода из текущего помещения нет.",
                reply_markup=keyboard_for(current),
            )

    return Bot(bot_token()), dp


def load_questions(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        (item["question"], str(item["answer"]).strip().casefold())
        for item in data
    ]


def create_quiz_bot():
    dp = Dispatcher()
    sessions = {}
    questions_path = Path(__file__).with_name("quiz_questions.json")
    start_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пройти опрос")]],
        resize_keyboard=True,
    )

    async def ask_next(message):
        session = sessions[message.chat.id]
        if session["index"] == len(session["questions"]):
            score = session["score"]
            total = len(session["questions"])
            sessions.pop(message.chat.id, None)
            await message.answer(
                f"Правильных ответов: {score} из {total}.",
                reply_markup=start_keyboard,
            )
            return
        question, _ = session["questions"][session["index"]]
        await message.answer(question, reply_markup=ReplyKeyboardRemove())

    async def start_quiz(message):
        questions = load_questions(questions_path)
        selected = random.sample(questions, k=min(10, len(questions)))
        sessions[message.chat.id] = {
            "questions": selected,
            "index": 0,
            "score": 0,
        }
        await ask_next(message)

    @dp.message(Command("start"))
    async def start(message):
        await message.answer(
            "Можно пройти опрос из 10 вопросов.",
            reply_markup=start_keyboard,
        )

    @dp.message(Command("stop"))
    async def stop(message):
        sessions.pop(message.chat.id, None)
        await message.answer("Опрос остановлен.", reply_markup=start_keyboard)

    @dp.message(F.text == "Пройти опрос")
    async def quiz_button(message):
        await start_quiz(message)

    @dp.message(F.text)
    async def answer(message):
        session = sessions.get(message.chat.id)
        if not session:
            await message.answer(
                "Нажмите /start, чтобы начать.",
                reply_markup=start_keyboard,
            )
            return
        _, correct = session["questions"][session["index"]]
        if message.text.strip().casefold() == correct:
            session["score"] += 1
        session["index"] += 1
        await ask_next(message)

    return Bot(bot_token()), dp


def create_geocoder_bot():
    dp = Dispatcher()

    @dp.message(F.text)
    async def geocode(message):
        try:
            result = await asyncio.to_thread(yandex_geocode, message.text)
        except Exception as exc:
            await message.answer(f"Ошибка геокодера: {exc}")
            return
        if result is None:
            await message.answer("Ничего не найдено.")
            return
        name, description, lon, lat = result
        caption = f"{name}\n{description}\nКоординаты: {lat:.6f}, {lon:.6f}"
        await message.answer_photo(
            yandex_static_map_url(lon, lat),
            caption=caption,
        )

    return Bot(bot_token()), dp


def create_translator_bot():
    dp = Dispatcher()
    directions = {}
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="ru -> en"),
                KeyboardButton(text="en -> ru"),
            ]
        ],
        resize_keyboard=True,
    )

    @dp.message(Command("start"))
    async def start(message):
        directions[message.chat.id] = ("ru", "en")
        await message.answer(
            "Выберите направление перевода.",
            reply_markup=keyboard,
        )

    @dp.message(F.text.in_({"ru -> en", "en -> ru"}))
    async def set_direction(message):
        directions[message.chat.id] = tuple(message.text.split(" -> "))
        await message.answer(
            f"Направление: {message.text}",
            reply_markup=keyboard,
        )

    @dp.message(F.text)
    async def handle_text(message):
        source, target = directions.get(message.chat.id, ("ru", "en"))
        try:
            translated = await translate_text(message.text, source, target)
        except Exception as exc:
            await message.answer(
                f"Ошибка перевода: {exc}",
                reply_markup=keyboard,
            )
            return
        await message.answer(translated, reply_markup=keyboard)

    return Bot(bot_token()), dp


def create_price_bot():
    dp = Dispatcher()

    @dp.message(Command("price"))
    async def price(message):
        args = message.text.split(maxsplit=1)
        if len(args) != 2:
            await message.answer("Использование: /price 42.50")
            return
        try:
            target = float(args[1].replace(",", "."))
            product = await asyncio.to_thread(closest_product, target)
        except Exception as exc:
            await message.answer(f"Не удалось подобрать товар: {exc}")
            return
        caption = (
            f"{product.name}\n"
            f"{product.description}\n"
            f"Цена: ${product.price:.2f}"
        )
        await message.answer_photo(product.image, caption=caption)

    return Bot(bot_token()), dp
