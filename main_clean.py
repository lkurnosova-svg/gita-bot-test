import json
import os
import random
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

with open("chapter1.json", "r", encoding="utf-8") as f:
    CHAPTER1 = json.load(f)

LANG_LABELS = {"RU": "Русский", "EN": "English", "BOTH": "RU + EN"}
LEVEL_LABELS = {
    "1": "Level 1 — с подсказками",
    "2": "Level 2 — без подсказок",
    "3": "Level 3 — IAST / санскрит",
}

USER_STATE = {}

def get_state(chat_id):
    if chat_id not in USER_STATE:
        USER_STATE[chat_id] = {
            "language": "BOTH",
            "level": "1",
            "chapter": "1",
            "current_card": None,
        }
    return USER_STATE[chat_id]

def api(method, params=None):
    if params is None:
        params = {}
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(f"{API_URL}/{method}", data=data)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def keyboard(rows):
    return json.dumps({"inline_keyboard": rows}, ensure_ascii=False)

def send_message(chat_id, text, reply_markup=None):
    params = {"chat_id": chat_id, "text": text}
    if reply_markup:
        params["reply_markup"] = reply_markup
    return api("sendMessage", params)

def edit_message(chat_id, message_id, text, reply_markup=None):
    params = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup:
        params["reply_markup"] = reply_markup
    return api("editMessageText", params)

def answer_callback(callback_id):
    try:
        api("answerCallbackQuery", {"callback_query_id": callback_id})
    except Exception:
        pass

def main_menu():
    return keyboard([
        [{"text": "📖 Глава 1", "callback_data": "chapter:1"}],
        [
            {"text": "🌐 Язык", "callback_data": "menu:language"},
            {"text": "🎚 Уровень", "callback_data": "menu:level"},
        ],
        [{"text": "▶️ Начать карточки", "callback_data": "card:next"}],
    ])

def language_menu():
    return keyboard([
        [
            {"text": "RU", "callback_data": "lang:RU"},
            {"text": "EN", "callback_data": "lang:EN"},
            {"text": "RU + EN", "callback_data": "lang:BOTH"},
        ],
        [{"text": "⬅️ Назад", "callback_data": "menu:main"}],
    ])

def level_menu():
    return keyboard([
        [{"text": "Level 1 — подсказки", "callback_data": "level:1"}],
        [{"text": "Level 2 — без подсказок", "callback_data": "level:2"}],
        [{"text": "Level 3 — IAST", "callback_data": "level:3"}],
        [{"text": "⬅️ Назад", "callback_data": "menu:main"}],
    ])

def card_buttons(show_answer=False):
    if not show_answer:
        return keyboard([
            [{"text": "👁 Показать ответ", "callback_data": "card:answer"}],
            [{"text": "➡️ Дальше", "callback_data": "card:next"}],
            [{"text": "⚙️ Настройки", "callback_data": "menu:main"}],
        ])
    return keyboard([
        [
            {"text": "✅ Знаю", "callback_data": "card:next"},
            {"text": "🔁 Повторить", "callback_data": "card:repeat"},
        ],
        [{"text": "⚙️ Настройки", "callback_data": "menu:main"}],
    ])

def lang_text(v, lang):
    if lang == "RU":
        return f"RU:\n{v['ru']}"
    if lang == "EN":
        return f"EN:\n{v['en']}"
    return f"RU:\n{v['ru']}\n\nEN:\n{v['en']}"

def make_card(state):
    v = random.choice(CHAPTER1)
    lang = state["language"]
    level = state["level"]

    if level == "1":
        templates = ["guided_verse", "structure", "meaning", "continue_ru_en"]
    elif level == "2":
        templates = ["independent_verse", "structure", "meaning", "continue_ru_en"]
    else:
        templates = ["iast_continue", "iast_to_structure", "iast_to_verse"]

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
    else:
        front = f"Назови номер стиха по IAST:\n\n{v['iast']}"
        back = f"{v['verse']}\n\n{lang_text(v, lang)}"

    return {"front": front, "back": back}

def show_start(chat_id):
    state = get_state(chat_id)
    text = (
        "Бот для теста карточек по Бхагавад-гите.\n\n"
        f"Глава: {state['chapter']}\n"
        f"Язык: {LANG_LABELS[state['language']]}\n"
        f"Уровень: {LEVEL_LABELS[state['level']]}\n\n"
        "Выберите настройки или начните карточки."
    )
    send_message(chat_id, text, main_menu())

def handle_callback(callback):
    answer_callback(callback["id"])
    data = callback["data"]
    message = callback["message"]
    chat_id = message["chat"]["id"]
    message_id = message["message_id"]
    state = get_state(chat_id)

    if data == "menu:main":
        text = (
            "Настройки:\n\n"
            f"Глава: {state['chapter']}\n"
            f"Язык: {LANG_LABELS[state['language']]}\n"
            f"Уровень: {LEVEL_LABELS[state['level']]}"
        )
        edit_message(chat_id, message_id, text, main_menu())
    elif data == "menu:language":
        edit_message(chat_id, message_id, "Выберите язык:", language_menu())
    elif data == "menu:level":
        edit_message(chat_id, message_id, "Выберите уровень:", level_menu())
    elif data.startswith("lang:"):
        state["language"] = data.split(":")[1]
        edit_message(chat_id, message_id, f"Язык выбран: {LANG_LABELS[state['language']]}", main_menu())
    elif data.startswith("level:"):
        state["level"] = data.split(":")[1]
        edit_message(chat_id, message_id, f"Уровень выбран: {LEVEL_LABELS[state['level']]}", main_menu())
    elif data.startswith("chapter:"):
        state["chapter"] = "1"
        edit_message(chat_id, message_id, "Пока в тесте доступна Глава 1.", main_menu())
    elif data == "card:next":
        state["current_card"] = make_card(state)
        edit_message(chat_id, message_id, state["current_card"]["front"], card_buttons(False))
    elif data == "card:repeat":
        if not state["current_card"]:
            state["current_card"] = make_card(state)
        edit_message(chat_id, message_id, state["current_card"]["front"], card_buttons(False))
    elif data == "card:answer":
        if not state["current_card"]:
            state["current_card"] = make_card(state)
        text = f"{state['current_card']['front']}\n\n———\n\nОтвет:\n{state['current_card']['back']}"
        edit_message(chat_id, message_id, text, card_buttons(True))

def poll():
    offset = None
    print("Bot is running...", flush=True)
    while True:
        try:
            params = {"timeout": 25}
            if offset is not None:
                params["offset"] = offset
            query = urllib.parse.urlencode(params)
            with urllib.request.urlopen(f"{API_URL}/getUpdates?{query}", timeout=35) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            for update in result.get("result", []):
                offset = update["update_id"] + 1
                if "message" in update:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "")
                    if text.startswith("/start"):
                        show_start(chat_id)
                    else:
                        send_message(chat_id, "Напишите /start, чтобы открыть меню.")
                elif "callback_query" in update:
                    handle_callback(update["callback_query"])
        except Exception as e:
            print(f"Polling error: {e}", flush=True)
            time.sleep(5)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bhagavad Gita bot is running")

    def log_message(self, format, *args):
        return

def start_web_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"Health server running on port {port}", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    Thread(target=start_web_server, daemon=True).start()
    poll()
