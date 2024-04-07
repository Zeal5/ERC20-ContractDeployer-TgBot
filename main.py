from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# internal imports
from cogs.menu import menu_convo_handler
from cogs.Wallet import db_startup

# std imports 
import os


load_dotenv()

API = os.environ.get("API") or "NoTokenFound"

async def at_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != 1617244632:
        return
    
    creating_db = context.application.create_task(db_startup())
    await creating_db 
    if update.message is not None and update.effective_user is not None:
        await update.message.reply_text(f'db has been created {update.effective_user.id}{update.effective_user.first_name}')


def main():
    app = ApplicationBuilder().token(API).build()
    app.add_handler(CommandHandler("createdb",at_start))

    # add cogs here 
    app.add_handler(menu_convo_handler,1)

    app.run_polling(0.1)

if __name__ == "__main__":
    main()
