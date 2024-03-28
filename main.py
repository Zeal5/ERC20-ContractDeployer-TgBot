from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# internal imports
from cogs.menu import menu_convo_handler

# std imports 
import os

load_dotenv()

API = os.environ.get("API") or "NoTokenFound"

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')


def main():
    app = ApplicationBuilder().token(API).build()
    app.add_handler(CommandHandler("hello", hello))

    # add cogs here 
    app.add_handler(menu_convo_handler,1)

    app.run_polling(0.1)

if __name__ == "__main__":
    main()
