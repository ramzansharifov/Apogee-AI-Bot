# Apogee AI Bot

**Apogee AI Bot** — это Telegram-бот, подключённый к локальной нейронке через **LM Studio**.  
Бот работает через OpenAI-compatible API и отвечает в фирменном стиле абсурдно-ностальгического советского ИИ-диктора: **тихо, не спеша, с лёгкой иронией**.

Ссылка на бота: [@apogee_ai_bot](https://t.me/apogee_ai_bot)

---

## Возможности

- Подключение к локальной модели через **LM Studio**
- Работа через Telegram
- Поддержка истории диалога для каждого чата
- Защита от пустых ответов модели
- Попытка отключения `thinking/reasoning mode`
- Единый стиль ответов: советский AI-мем-диктор
- Команда для очистки истории диалога

---

## Стек

- Python
- python-telegram-bot
- OpenAI Python SDK
- LM Studio
- dotenv

---

## Установка

Склонируйте репозиторий:

```bash
git clone https://github.com/ramzansharifov/Apogee-AI-Bot.git
cd Apogee-AI-Bot
```

Создайте виртуальное окружение:

```bash
python -m venv .venv
```

Активируйте его.

Для Windows:

```bash
.venv\Scripts\activate
```

Для macOS/Linux:

```bash
source .venv/bin/activate
```

Установите зависимости:

```bash
pip install -r requirements.txt
```

---

## Настройка `.env`

Создайте файл `.env` в корне проекта:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=your_model_name_here
```

Важно: файл `.env` нельзя загружать на GitHub, потому что внутри находится токен Telegram-бота.

---

## Запуск LM Studio

1. Откройте **LM Studio**.
2. Загрузите нужную модель.
3. Перейдите во вкладку **Local Server**.
4. Запустите сервер.
5. Убедитесь, что адрес работает:

```text
http://localhost:1234/v1/models
```

---

## Запуск бота

```bash
python bot.py
```

После запуска в терминале должно появиться:

```text
Bot is running...
```

Теперь можно открыть Telegram и написать боту: [@apogee_ai_bot](https://t.me/apogee_ai_bot)

---

## Команды бота

```text
/start
```

Показывает приветствие и краткое описание бота.

```text
/clear
```

Очищает историю текущего диалога.

---

## Стиль ответов

Бот отвечает не как обычный помощник, а в стиле ироничного советского AI-диктора.  
Он сохраняет пользу ответа, но добавляет фирменную интонацию:

> Тихо, не спеша. Черемша.

Пример:

```text
Python — это язык программирования, на котором удобно писать ботов, сайты, скрипты и нейросети. Синтаксис простой, поэтому новичку легче войти в код. Всё спокойно: сначала переменные, потом функции, потом победа. Тихо, не спеша. Черемша.
```

---

## Безопасность

Перед публикацией проекта убедитесь, что в репозиторий не попали:

```text
.env
.venv/
__pycache__/
.idea/
```

Для этого в проекте должен быть файл `.gitignore`.

Пример `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.pyc
.idea/
```

---

## Автор

Проект создан как локальный Telegram AI-бот для экспериментов с LM Studio, стилями общения и локальными языковыми моделями.

Бот: [@apogee_ai_bot](https://t.me/apogee_ai_bot)

