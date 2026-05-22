import argparse
import asyncio
import sys
from pathlib import Path


if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))


BOT_NAMES = (
    "board",
    "echo",
    "geocoder",
    "museum",
    "price",
    "quiz",
    "time",
    "translator",
)


def bot_factories():
    from telegram_bots.factories import create_board_game_bot
    from telegram_bots.factories import create_echo_bot, create_geocoder_bot
    from telegram_bots.factories import create_museum_bot, create_price_bot
    from telegram_bots.factories import create_quiz_bot, create_time_date_bot
    from telegram_bots.factories import create_translator_bot

    return {
        "echo": create_echo_bot,
        "time": create_time_date_bot,
        "board": create_board_game_bot,
        "museum": create_museum_bot,
        "quiz": create_quiz_bot,
        "geocoder": create_geocoder_bot,
        "translator": create_translator_bot,
        "price": create_price_bot,
    }


def selected_factory(name):
    try:
        return bot_factories()[name]
    except ModuleNotFoundError as exc:
        if exc.name == "aiogram":
            raise RuntimeError(
                "Install dependencies first: pip install -r requirements.txt"
            ) from exc
        raise


async def run_bot(name):
    bot, dispatcher = selected_factory(name)()
    await dispatcher.start_polling(bot)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("bot", choices=BOT_NAMES)
    return parser.parse_args()


def main():
    args = parse_args()
    asyncio.run(run_bot(args.bot))


if __name__ == "__main__":
    main()
