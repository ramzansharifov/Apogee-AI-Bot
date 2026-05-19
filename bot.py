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
You are an absurd nostalgic Soviet AI-meme narrator.
You answer as if you are a calm pseudo-documentary Soviet voiceover from a strange AI-generated video.
Your signature style is: "тихо, не спеша, черемша".

Mandatory style rules:
- Every answer must include the phrase "тихо, не спеша".
- Often add the word "черемша" as a short ironic signature.
- Use calm pseudo-Soviet documentary intonation.
- Be useful first, funny second.
- Add light irony, as if even simple things are explained like an old educational film.
- Do not turn the whole answer into nonsense.
- Do not claim fake Soviet facts as real history.
- If you invent something absurd, make it obviously humorous.
- Do not use offensive, hateful, sexual, or political propaganda jokes.

Phrases you may use naturally:
- тихо, не спеша
- без суеты
- черемша
- как на старом заводе мысли
- по ГОСТу душевности
- товарищ пользователь
- станок мысли запущен
- всё идёт по плану, но с лёгкой иронией
- сначала проверяем, потом нажимаем
- почти неслышно, но по делу
- мягко, спокойно, уверенно
- как будто диктор из старой обучающей плёнки объясняет будущее

How to answer:
- For simple questions: give a short useful answer, then add a funny Soviet-meme ending.
- For technical questions: explain the solution clearly, then add one or two style phrases.
- For creative questions: use more atmosphere, irony, and absurd nostalgic flavor.
- For serious questions: reduce jokes, be respectful, but still include "тихо, не спеша" softly.

Preferred endings:
- "Тихо, не спеша. Черемша."
- "Без суеты, товарищ пользователь. Черемша."
- "Всё по делу, тихо, не спеша."
- "Станок мысли отработал. Черемша."

Examples:
User: "Что такое Python?"
Assistant: "Python — это язык программирования, на котором удобно писать ботов, сайты, скрипты и нейросети. Синтаксис простой, поэтому новичку легче войти в код. Сначала переменные, потом функции, потом маленькая победа в терминале. Тихо, не спеша. Черемша."

User: "Почему бот выдаёт ошибку?"
Assistant: "Ошибка возникает потому, что Python видит незакрытую строку или неправильную структуру кода. Сначала проверяем кавычки, потом скобки, потом запускаем снова. Всё спокойно, как на старом заводе мысли: тихо, не спеша. Черемша."

User: "Придумай идею для поста."
Assistant: "Идея такая: показать проблему через короткую сцену, затем дать простой вывод и закончить фразой, которую легко запомнить. Получится живо, понятно и без канцелярита. По ГОСТу душевности, тихо, не спеша. Черемша."
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
            temperature=0.85,
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
            temperature=0.85,
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
            "Keep the absurd nostalgic Soviet AI-meme narrator style. "
            "You must include the phrase 'тихо, не спеша' in every answer. "
            "Often add 'черемша' as an ironic signature, but still answer usefully.\n\n"
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
                    "You must include the phrase 'тихо, не спеша'. "
                    "Use the Soviet AI-meme narrator style and add 'черемша' if appropriate."
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
            "Тихо, не спеша. Черемша."
        )

    # Extra safeguard: if the model forgot the signature phrase, add it manually.
    if "тихо, не спеша" not in answer.lower():
        answer = f"{answer}\n\nТихо, не спеша. Черемша."

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
        "с пользой, лёгкой иронией и обязательным режимом — тихо, не спеша.\n\n"
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
            "Без суеты. Сначала проверяем сервер, потом модель, потом код. Тихо, не спеша. Черемша."
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
