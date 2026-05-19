import os
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is missing in the .env file.")

if not LM_STUDIO_BASE_URL:
    raise ValueError("LM_STUDIO_BASE_URL is missing in the .env file.")

if not LM_STUDIO_MODEL:
    raise ValueError("LM_STUDIO_MODEL is missing in the .env file.")


client = OpenAI(
    base_url=LM_STUDIO_BASE_URL,
    api_key="lm-studio"
)


chat_histories = {}


SYSTEM_PROMPT = """
/no_think

You are a local AI assistant connected to a Telegram bot through LM Studio.

Critical technical rules:
- Thinking mode is disabled.
- Do not use reasoning mode.
- Do not write internal reasoning.
- Do not write a thinking process.
- Do not explain your hidden thoughts.
- Give only the final answer.
- Never send an empty answer.
- If the user writes in Russian, answer in Russian.
- If the user writes in English, answer in English.
- Do not make answers too long unless the user asks for details.

Main personality:
You always answer in the style of an absurd nostalgic Soviet AI-meme narrator.
This style is inspired by phrases like: "В Советском Союзе всё делали тихо, не спеша, черемша."

Tone and style:
- Sound like a calm, serious, pseudo-documentary narrator.
- Add absurd Soviet-style nostalgia, but keep the answer useful.
- Always add the phrase "тихо, не спеша" somewhere in the answer.
- Add it with light irony, as if it is the bot's signature phrase.
- Use short funny phrases like: "тихо, не спеша", "без суеты", "как на старом заводе", "по ГОСТу душевности", "черемша".
- Use this style naturally, not in every sentence.
- Be funny, but do not turn every answer into nonsense.
- First help the user, then add the meme flavor.
- Avoid offensive jokes, hate, propaganda, or real political agitation.
- Do not claim false historical facts as real facts.
- If you invent absurd Soviet facts for humor, make it obvious that it is a joke.

Answer structure:
- For simple questions: answer briefly and with meme flavor.
- For technical questions: explain clearly, then add light meme flavor.
- For serious topics: reduce jokes, answer respectfully, and add the phrase "тихо, не спеша" softly and without mockery.
- Prefer ending many answers with a short ironic signature, for example: "Тихо, не спеша. Черемша."

Examples in Russian:
User: "Что такое Python?"
Assistant: "Python — это язык программирования, на котором удобно писать ботов, сайты, скрипты и нейросети. Синтаксис простой, поэтому новичку легче войти в код. В Советском Союзе такой язык назвали бы: работает тихо, не спеша, но дело делает. Черемша."

User: "Почему бот выдаёт ошибку?"
Assistant: "Ошибка возникает потому, что модель не вернула обычный текстовый ответ. Код ждёт content, а модель могла уйти в reasoning mode. Значит, надо отключить thinking и добавить защиту от пустого ответа. Всё спокойно: сначала проверяем сервер, потом модель, потом код. Тихо, не спеша, как на заводе точной мысли."

User: "Придумай идею для поста."
Assistant: "Идея такая: показать проблему через короткую сцену, потом дать простой вывод и закончить сильной фразой. Получится живо, понятно и без канцелярита. По ГОСТу душевности, без суеты, черемша."
"""


def get_history(chat_id: int):
    if chat_id not in chat_histories:
        chat_histories[chat_id] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

    return chat_histories[chat_id]


def reset_history(chat_id: int):
    chat_histories[chat_id] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]


def trim_history(history, max_messages: int = 8):
    system_message = history[0]
    recent_messages = history[1:][-max_messages:]
    return [system_message] + recent_messages


def extract_answer(response) -> str:
    message = response.choices[0].message

    answer = getattr(message, "content", None)

    if answer and answer.strip():
        return answer.strip()

    # Some local servers may store additional fields in model_dump().
    if hasattr(message, "model_dump"):
        message_data = message.model_dump()
        answer = message_data.get("content")

        if answer and answer.strip():
            return answer.strip()

    return ""


def create_completion(messages, max_tokens: int = 700):
    """
    First attempt: try to disable thinking mode through extra_body.
    If LM Studio does not support this parameter, retry without it.
    """

    try:
        return client.chat.completions.create(
            model=LM_STUDIO_MODEL,
            messages=messages,
            temperature=0.75,
            max_tokens=max_tokens,
            extra_body={
                "chat_template_kwargs": {
                    "enable_thinking": False
                }
            }
        )
    except Exception:
        return client.chat.completions.create(
            model=LM_STUDIO_MODEL,
            messages=messages,
            temperature=0.75,
            max_tokens=max_tokens
        )


def ask_local_ai(chat_id: int, user_text: str) -> str:
    history = get_history(chat_id)

    history.append({
        "role": "user",
        "content": (
            "/no_think\n"
            "Answer with the final answer only. "
            "Do not think step by step. "
            "Do not write reasoning. "
            "Do not write analysis. "
            "Keep the Soviet AI-meme narrator style, but still answer usefully. "
            "Always include the phrase 'тихо, не спеша' with light irony.\n\n"
            f"{user_text}"
        )
    })

    history = trim_history(history)
    chat_histories[chat_id] = history

    response = create_completion(history, max_tokens=700)
    answer = extract_answer(response)

    # Second attempt if the model returned empty content.
    if not answer:
        retry_messages = history + [
            {
                "role": "user",
                "content": (
                    "/no_think\n"
                    "Your previous answer was empty. "
                    "Now give ONLY the final answer in plain text. "
                    "No reasoning. No thinking process. No analysis. "
                    "Use the Soviet AI-meme narrator style."
                )
            }
        ]

        retry_response = create_completion(retry_messages, max_tokens=400)
        answer = extract_answer(retry_response)

    if not answer:
        answer = (
            "Модель снова ушла в thinking/reasoning mode и не вернула обычный текстовый ответ.\n\n"
            "Код работает, но текущая модель отдаёт рассуждение отдельно от финального ответа. "
            "Попробуй повторить вопрос короче, отключить thinking mode в LM Studio "
            "или выбрать модель без reasoning/thinking режима.\n\n"
            "Тихо, не спеша, черемша."
        )

    history.append({
        "role": "assistant",
        "content": answer
    })

    chat_histories[chat_id] = trim_history(history)

    return answer


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте, товарищ пользователь.\n\n"
        "Я локальный Telegram-бот через LM Studio. Отвечаю в стиле советского ИИ-диктора: "
        "тихо, не спеша, с лёгким абсурдом и пользой для дела.\n\n"
        "Команды:\n"
        "/clear — очистить историю диалога\n\n"
        "Задавайте вопрос. Черемша."
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    reset_history(chat_id)

    await update.message.reply_text(
        "История диалога очищена. Мы снова начинаем с чистого листа, тихо, не спеша. Черемша."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = update.message.text

    await context.bot.send_chat_action(
        chat_id=chat_id,
        action=ChatAction.TYPING
    )

    try:
        answer = await asyncio.to_thread(ask_local_ai, chat_id, user_text)

        if len(answer) <= 4000:
            await update.message.reply_text(answer)
        else:
            for i in range(0, len(answer), 4000):
                await update.message.reply_text(answer[i:i + 4000])

    except Exception as error:
        await update.message.reply_text(
            "Ошибка при обращении к локальной нейронке.\n\n"
            "Проверь:\n"
            "1. LM Studio открыт.\n"
            "2. Local Server запущен.\n"
            "3. Модель загружена.\n"
            "4. Адрес http://localhost:1234/v1/models открывается в браузере.\n\n"
            f"Техническая ошибка: {error}\n\n"
            "Без суеты. Сначала проверяем сервер, потом модель, потом код. Черемша."
        )


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
