from telegram import Update
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes,CallbackQueryHandler
from dotenv import load_dotenv

# internal imports
from cogs.menu_handler.menu import menu_convo_handler
from cogs.menu_handler.TransferTokens.transfer import transfer_tokens_convo_handler
from cogs.DataBase import db_startup

# std imports 
import os, base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


load_dotenv()

API = os.environ.get("API") or "NoTokenFound"

async def at_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != 1617244632:
        return
    
    creating_db = context.application.create_task(db_startup())
    await creating_db 
    if update.message is not None and update.effective_user is not None:
        await update.message.reply_text(f'db has been created {update.effective_user.id}{update.effective_user.first_name}')

async def set_encryption_key(update :Update, context:ContextTypes.DEFAULT_TYPE):
    _key = update.message.text
    paswd = _key.strip().split()[-1]
    print(paswd)
    salt = b'salty_'  
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,  # Number of iterations
        backend=default_backend()
    )
    key = kdf.derive(paswd.encode())
    os.environ['KEY'] = base64.urlsafe_b64encode(key).decode('utf-8')



def main():
    app = ApplicationBuilder().token(API).build()
    app.add_handler(CommandHandler("createdb",at_start))
    app.add_handler(CommandHandler("key", set_encryption_key))

    # add cogs here 
    app.add_handler(menu_convo_handler,1)
    app.add_handler(transfer_tokens_convo_handler,2)

    app.run_polling(0.1)

if __name__ == "__main__":
    main()
