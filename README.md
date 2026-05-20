# Bhagavad Gita Flashcards — Telegram Bot Prototype

Тестовый бот для первой главы Бхагавад-гиты.

## Что умеет

- выбор языка: RU / EN / RU + EN
- выбор уровня:
  - Level 1 — с подсказкой главы
  - Level 2 — без подсказки главы
  - Level 3 — IAST / санскрит
- карточки:
  - назови номер стиха
  - к какой подглаве относится стих
  - что происходит в стихе
  - дополни фразу
  - дополни шлоку по IAST

## Как запустить

### 1. Создать бота в Telegram

1. Откройте Telegram.
2. Найдите `@BotFather`.
3. Отправьте команду `/newbot`.
4. Дайте имя и username.
5. BotFather выдаст токен.

### 2. Установить Python

Нужен Python 3.10+.

### 3. Установить зависимости

В папке проекта:

```bash
pip install -r requirements.txt
```

### 4. Запустить бота

Mac/Linux:

```bash
export BOT_TOKEN="ваш_токен_от_BotFather"
python bot.py
```

Windows PowerShell:

```powershell
$env:BOT_TOKEN="ваш_токен_от_BotFather"
python bot.py
```

### 5. Открыть бота в Telegram

Нажмите `/start`.

## Важно

Это тестовая версия. Данные первой главы сокращены для удобства сообщений в Telegram. Позже можно подключить полные тексты из master-таблицы и добавить MainIdea, аудио, деванагари и статистику повторений.
