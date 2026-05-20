import json
import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

with open("data/chapter1.json", "r", encoding="utf-8") as f:
    CHAPTER1 = json.load(f)

LANG_LABELS = {
    "RU": "Русский",
    "EN": "English",
    "BOTH": "RU + EN",
}

LEVEL_LABELS = {
    "1": "Level 1 — с подсказками",
    "2": "Level 2 — без подсказок",
    "3": "Level 3 — IAST / санскрит",
}

@dataclass
class UserState:
    language: str = "BOTH"
    level: str = "1"
    chapter: str = "1"
    current_card: Dict[str, Any] = field(default_factory=dict)

USER_STATE: Dict[int, UserState] = {}

def state_for(user_id: int) -> UserState:
    if user_id not in USER_STATE:
        USER_STATE[user_id] = UserState()
    return USER_STATE[user_id]

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Глава 1", callback_data="chapter:1")],
        [InlineKeyboardButton("🌐 Язык", callback_data="menu:language"),
         InlineKeyboardButton("🎚 Уровень", callback_data="menu:level")],
        [InlineKeyboardButton("▶️ Начать карточки", callback_data="card:next")],
    ])

def language_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("RU", callback_data="lang:RU"),
         InlineKeyboardButton("EN", callback_data="lang:EN"),
         InlineKeyboardButton("RU + EN", callback_data="lang:BOTH")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu:main")]
    ])

def level_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Level 1 — подсказки", callback_data="level:1")],
        [InlineKeyboardButton("Level 2 — без подсказок", callback_data="level:2")],
        [InlineKeyboardButton("Level 3 — IAST", callback_data="level:3")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu:main")]
    ])

def card_buttons(show_answer: bool = False) -> InlineKeyboardMarkup:
    if not show_answer:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("👁 Показать ответ", callback_data="card:answer")],
            [InlineKeyboardButton("➡️ Дальше", callback_data="card:next")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="menu:main")]
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Знаю", callback_data="card:next"),
         InlineKeyboardButton("🔁 Повторить", callback_data="card:repeat")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="menu:main")]
    ])

def lang_text(v: Dict[str, str], lang: str) -> str:
    if lang == "RU":
        return f"RU:\n{v['ru']}"
    if lang == "EN":
        return f"EN:\n{v['en']}"
    return f"RU:\n{v['ru']}\n\nEN:\n{v['en']}"

def make_card(state: UserState) -> Dict[str, str]:
    v = random.choice(CHAPTER1)
    lang = state.language
    level = state.level

    # Level 1: with chapter hint.
    if level == "1":
        templates = [
            "guided_verse",
            "structure",
            "meaning",
            "continue_ru_en",
        ]
    elif level == "2":
        templates = [
            "independent_verse",
            "structure",
            "meaning",
            "continue_ru_en",
        ]
    else:
        templates = [
            "iast_continue",
            "iast_to_structure",
            "iast_to_verse",
        ]

    t = random.choice(templates)

    if t == "guided_verse":
        front = f"Глава 1.\nНазови номер стиха.\n\n{lang_text(v, lang)}"
        back = f"{v['verse']}\n\nПодглава:\n{v['sub_ru']}\n{v['sub_en']}"

    elif t == "independent_verse":
        front = f"Назови номер стиха.\n\n{lang_text(v, lang)}"
        back = f"{v['verse']}\n\nПодглава:\n{v['sub_ru']}\n{v['sub_en']}"

    elif t == "structure":
        front = f"К какой подглаве относится этот стих?\n\n{lang_text(v, lang)}"
        back = f"{v['sub_ru']}\n{v['sub_en']}\n\nVerse: {v['verse']}"

    elif t == "meaning":
        front = f"Что происходит в этом стихе?\n\n{lang_text(v, lang)}"
        back = f"Кратко:\n{v['ru']}\n\nVerse: {v['verse']}"

    elif t == "continue_ru_en":
        if lang == "EN":
            first = v["en"].split(",")[0].split(".")[0]
            front = f"Complete the phrase:\n\n{first}..."
            back = f"{v['en']}\n\nVerse: {v['verse']}"
        elif lang == "RU":
            first = v["ru"].split(",")[0].split(".")[0]
            front = f"Дополни фразу:\n\n{first}..."
            back = f"{v['ru']}\n\nСтих: {v['verse']}"
        else:
            ru_first = v["ru"].split(",")[0].split(".")[0]
            en_first = v["en"].split(",")[0].split(".")[0]
            front = f"Дополни фразу / Complete the phrase:\n\nRU:\n{ru_first}...\n\nEN:\n{en_first}..."
            back = f"RU:\n{v['ru']}\n\nEN:\n{v['en']}\n\nVerse: {v['verse']}"

    elif t == "iast_continue":
        front = f"Дополни шлоку до конца:\n\n{v['iast']}..."
        back = f"IAST:\n{v['iast']}\n\n{lang_text(v, lang)}\n\nVerse: {v['verse']}"

    elif t == "iast_to_structure":
        front = f"К какой подглаве относится эта шлока?\n\nIAST:\n{v['iast']}"
        back = f"{v['sub_ru']}\n{v['sub_en']}\n\nVerse: {v['verse']}"

    else: # iast_to_verse
        front = f"Назови номер стиха по IAST:\n\n{v['iast']}"
        back = f"{v['verse']}\n\n{lang_text(v, lang)}"

    return {"front": front, "back": back, "verse": v["verse"], "type": t}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = state_for(user_id)
    text = (
        "Бот для теста карточек по Бхагавад-гите.\n\n"
        f"Глава: {state.chapter}\n"
        f"Язык: {LANG_LABELS[state.language]}\n"
        f"Уровень: {LEVEL_LABELS[state.level]}\n\n"
        "Выберите настройки или начните карточки."
    )
    await update.message.reply_text(text, reply_markup=main_menu())

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    state = state_for(user_id)
    data = q.data

    if data == "menu:main":
        text = (
            "Настройки:\n\n"
            f"Глава: {state.chapter}\n"
            f"Язык: {LANG_LABELS[state.language]}\n"
            f"Уровень: {LEVEL_LABELS[state.level]}"
        )
        await q.edit_message_text(text, reply_markup=main_menu())
        return

    if data == "menu:language":
        await q.edit_message_text("Выберите язык:", reply_markup=language_menu())
        return

    if data == "menu:level":
        await q.edit_message_text("Выберите уровень:", reply_markup=level_menu())
        return

    if data.startswith("lang:"):
        state.language = data.split(":")[1]
        await q.edit_message_text(f"Язык выбран: {LANG_LABELS[state.language]}", reply_markup=main_menu())
        return

    if data.startswith("level:"):
        state.level = data.split(":")[1]
        await q.edit_message_text(f"Уровень выбран: {LEVEL_LABELS[state.level]}", reply_markup=main_menu())
        return

    if data.startswith("chapter:"):
        state.chapter = "1"
        await q.edit_message_text("Пока в тесте доступна Глава 1.", reply_markup=main_menu())
        return

    if data == "card:next":
        state.current_card = make_card(state)
        await q.edit_message_text(state.current_card["front"], reply_markup=card_buttons(show_answer=False))
        return

    if data == "card:repeat":
        if state.current_card:
            await q.edit_message_text(state.current_card["front"], reply_markup=card_buttons(show_answer=False))
        else:
            state.current_card = make_card(state)
            await q.edit_message_text(state.current_card["front"], reply_markup=card_buttons(show_answer=False))
        return

    if data == "card:answer":
        if not state.current_card:
            state.current_card = make_card(state)
        text = f"{state.current_card['front']}\n\n———\n\nОтвет:\n{state.current_card['back']}"
        await q.edit_message_text(text, reply_markup=card_buttons(show_answer=True))
        return

def main():
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN environment variable first.")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
