from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)


async def partial_menu(update: Update, context: CallbackContext):
    button1 = InlineKeyboardButton("Add Liq", callback_data="ADD_LIQ")
    button2 = InlineKeyboardButton("Lock tokens", callback_data="LOCK_LIQ")
    button3 = InlineKeyboardButton("BACK", callback_data="menu")

    keyboard = [[button1, button2], [button3]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Add liq or lock tokens"
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    return ConversationHandler.END


midway_convo_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(partial_menu, "partial")],
    states={},
    fallbacks=[],
)
