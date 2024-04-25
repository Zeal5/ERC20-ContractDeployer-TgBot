from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from .helpers import clean_token_address, transfer_eth,check_wallet_balance_from_tg_id
from cogs import RESTART

GET_ADDRESS, TRANSFER = range(2)


async def enter_transfer_wallet(update: Update, context: CallbackContext):
    text = (
        "Transfer eth to another address (this operation is not reversable\n"
        "address <SPACE> value (of ether)\n"
        "address <SPACE> all (to transfer all ether)\n"
        "0xaddress 0.25"
        "0xaddress all | All | ALL"
    )
    button = InlineKeyboardButton("MENU", callback_data="menu")
    keyboard = [[button]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=text, parse_mode="Markdown", reply_markup=reply_markup
    )
    return GET_ADDRESS


async def get_transfer_wallet(update: Update, context: CallbackContext):
    _reply = update.message.text
    address, value = clean_token_address(_reply)
    print(f"address,value {address}\t{value}")
    context.user_data["address"] = address
    context.user_data["value"] = value
    if value in ['all','All','ALL']:
        value = await check_wallet_balance_from_tg_id(update.effective_user.id)
        value = f'{float(value):.4f}'

    message = (
        "Transfering ETH Out of Wallet\n" f"To:```{address}```\n" f"VALUE:```{value}```"
    )
    button = InlineKeyboardButton("Procces", callback_data="yes_send")
    button1 = InlineKeyboardButton("Back", callback_data="transfer_funds")
    keyboard = [[button], [button1]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        update.effective_user.id,
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return TRANSFER


async def transfer_funds(update: Update, context: CallbackContext):
    address, value = context.user_data["address"], context.user_data["value"]
    try:
        transferd = await transfer_eth(address, value, update.effective_user.id)
        if not transferd:
            message = (
                f"Do not have enough balance to send"
            )
            await context.bot.send_message(
                update.effective_user.id,
                message,
                parse_mode="Markdown",
            )
            return ConversationHandler.END

        message = f"Funds transferd \n{transferd}"
        await context.bot.send_message(
            update.effective_user.id,
            message,
            parse_mode="Markdown",
            )
    except Exception as e:
        print(str(e))
        message = "Faild to transfer funds something went wrong"
        await context.bot.send_message(
            update.effective_user.id,
            message,
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    
        


async def stop(update: Update, context: CallbackContext):
    print("ending transfer funds convo")
    return ConversationHandler.END


transfer_tokens_convo_handler = ConversationHandler(
    # try passing block too MessageHandler to see if
    # it stil lets users use other commadns
    entry_points=[
        CallbackQueryHandler(enter_transfer_wallet, pattern="transfer_funds"),
    ],
    states={
        GET_ADDRESS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_transfer_wallet),
            CallbackQueryHandler(stop, "menu"),
        ],
        TRANSFER: [
            CallbackQueryHandler(transfer_funds, "yes_send"),
            CallbackQueryHandler(enter_transfer_wallet, pattern="transfer_funds"),
        ],
    },
    fallbacks=[
        MessageHandler(filters.TEXT | filters.COMMAND, stop),
        CommandHandler("stop", stop),
    ],
)
