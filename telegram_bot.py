from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Bot
from dotenv import load_dotenv
from telegram_client import send_message
import os

load_dotenv()

chat_ids = [str(id) for id in os.getenv('TELEGRAM_CHAT_IDS').split(',')]
telegram_token = os.getenv('TELEGRAM_TOKEN')

import vertexai
import inspect
from vertexai.generative_models import (
    GenerativeModel,
)
from gemini_toolbox import declarations
from gemini_toolbox import client
import gemini_investor

all_functions = [
    func
    for name, func in inspect.getmembers(gemini_investor, inspect.isfunction)
]

all_functions_tools = declarations.generate_tool_from_functions(all_functions)

from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    './sa.json')

vertexai.init(project="gemini-trading-backend", location="us-west1", credentials=credentials)

model = GenerativeModel(model_name="gemini-1.5-pro", tools=[all_functions_tools])

CLIENTS = {
}


async def start(update, context):
    if str(update.message.chat_id) not in chat_ids:
        return
    await update.message.reply_text('One sec, warming up.')


async def message(update, context):
    if update and update.message and str(update.message.chat_id) not in chat_ids:
        return
    clt = CLIENTS.get(update.message.chat_id, None)
    if not clt:
        clt = client.GeminiChatClient(all_functions, model, debug=False)
        CLIENTS[update.message.chat_id] = clt
    answer = clt.send_message(update.message.text)
    await update.message.reply_text(answer)


async def get_chat_id(update, context):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Your chat ID is: {chat_id}")


bot = Bot(token=telegram_token)


def main():
    print("starting")
    application = Application.builder().bot(bot).build()
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    get_chat_id_handler = CommandHandler('get_chat_id', get_chat_id)
    application.add_handler(get_chat_id_handler)    

    main_handler = MessageHandler(filters.TEXT, message)
    application.add_handler(main_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
