from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from time import time
from telegram.ext import (
    CallbackContext,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from cogs import WAIT_FOR_LIQ_ADDRESS, WAIT_LOCK_DURATION
from .helpers import MidWay


async def get_lp_token_address(update: Update, context: CallbackContext):
    button = InlineKeyboardButton("BACK", callback_data="menu")

    keyboard = [[button]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "Reply to this message with LP token address you want to Lock."
        "This only works if basuFactory already holds the LP tokens"
    )
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return WAIT_FOR_LIQ_ADDRESS


async def lock_lp(update: Update, context: CallbackContext):
    _reply = update.message.text.strip().split()[0]
    midway = MidWay(update.effective_user.id)
    try:
        is_address = midway.is_address(_reply)
        if is_address:
            factory_balance = await midway.get_balance(is_address)
            if factory_balance == 0:
                await context.bot.send_message(
                    update.effective_chat.id,
                    "Factory doesn't hold any LP tokens",
                )
                return ConversationHandler.END
    except Exception as e:
        print(str(e))
        await context.bot.send_message(
            update.effective_chat.id,
            "Wrong address.Try again",
        )
        return WAIT_FOR_LIQ_ADDRESS
    context.user_data["lp_token_address"] = is_address
    button1 = InlineKeyboardButton("1 WEEK", callback_data="1week")
    button2 = InlineKeyboardButton("15 DAYS", callback_data="15days")
    button3 = InlineKeyboardButton("1 MONTH", callback_data="1month")
    button4 = InlineKeyboardButton("1 YEAR", callback_data="1year")
    button5 = InlineKeyboardButton("Menu", callback_data="menu")

    # Combine the two buttons in a single row, each list represents a new row
    keyboard = [[button1, button2], [button3, button4], [button5]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        update.effective_chat.id, "SELECT LOCK DURATION", reply_markup=reply_markup
    )
    return WAIT_LOCK_DURATION


async def lock_lp_tokens(update: Update, context: CallbackContext):
    button = InlineKeyboardButton("BACK", callback_data="menu")

    keyboard = [[button]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query.data
    duration = 0
    if query is not None:
        match query:
            case "1week":
                duration = int(time()) + (7 * 24 * 60 * 60)
            case "15days":
                duration = int(time()) + (15 * 24 * 60 * 60)
            case "1month":
                duration = int(time()) + (30 * 24 * 60 * 60)
            case "1year":
                duration = int(time()) + (367 * 24 * 60 * 60)
    midway = MidWay(update.effective_user.id)
    lp_token_address = context.user_data["lp_token_address"]
    try:
        liq_lock_hash = await midway.lock_tokens(lp_token_address, duration)
    except Exception as e:
        print(str(e))
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            f"Something went wrong while locking tokens",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        f"Liq locked\ntxn Hash: ```{liq_lock_hash}```",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def random_response(update: Update, context: CallbackContext):
    text = (
        "Something Caused the conversation to end unexpectedly"
        "\n"
        "Terminating Chat\n"
        "Type `/menu` to access main menu"
    )
    await context.bot.send_message(
        update.effective_user.id, text, parse_mode="Markdown"
    )
    return ConversationHandler.END


async def stop(update: Update, context: CallbackContext):
    print("stping add liq conv handler")
    return ConversationHandler.END


lock_lp_convo_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(get_lp_token_address, "LOCK_LIQ"),
    ],
    states={
        WAIT_FOR_LIQ_ADDRESS: [
            CallbackQueryHandler(stop, "menu"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, lock_lp),
        ],
        WAIT_LOCK_DURATION: [
            CallbackQueryHandler(stop, "menu"),
            CallbackQueryHandler(lock_lp_tokens),
        ],
    },
    fallbacks=[],
)
