from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from cogs import WAIT_FOR_TOKEN_ADDRESS, WAIT_FOR_ETH_TO_ADD
from cogs.menu_handler.DeployToken import TokenLiqAdded, TxnHash
from .helpers import MidWay


async def get_token_address(update: Update, context: CallbackContext):
    button = InlineKeyboardButton("BACK", callback_data="menu")

    keyboard = [[button]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "Reply to this message with token address you want to add liq to."
        "This only works if basuFactory already holds the tokens"
        "\n"
        "0xAddress <SPACE> <eth to add to liq>"
        "\n"
        "0xAddress 5.6"
    )
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return WAIT_FOR_TOKEN_ADDRESS


async def prompt_liq_to_add(update: Update, context: CallbackContext):
    _reply = update.message.text.strip().split()
    # get token address and verify it
    _token_address = _reply[0]
    print(_token_address)
    midway = MidWay(update.effective_user.id)
    is_address = midway.is_address(_token_address)
    print(is_address)
    if not is_address:
        await context.bot.send_message(update.effective_chat.id, "Address is not Valid")
        return WAIT_FOR_TOKEN_ADDRESS
    factory_token_balance = await midway.get_balance(is_address)
    if factory_token_balance == 0:
        await context.bot.send_message(
            update.effective_chat.id, "Factry doesn't hold any tokens"
        )
        return ConversationHandler.END

    context.user_data["token_address"] = is_address
    # Check if user holds enouogh eth to add liq
    try:
        liq_to_add = float(_reply[1])
    except Exception as e:
        print(str(e))
        await context.bot.send_message(update.effective_chat.id, "Invalid Liq value")
        return WAIT_FOR_TOKEN_ADDRESS

    _user_balance = await midway.check_wallet_balance()
    if liq_to_add > _user_balance:
        await context.bot.send_message(
            update.effective_chat.id, "Not enuogh funds in wallet"
        )
        return WAIT_FOR_TOKEN_ADDRESS
    context.user_data["liq_to_add"] = liq_to_add

    # get eth to add to liq
    button = InlineKeyboardButton("Add liq", callback_data="yes_add_liq")
    button1 = InlineKeyboardButton("BACK", callback_data="back")
    button2 = InlineKeyboardButton("MENU", callback_data="menu")
    keyboard = [[button], [button1, button2]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"Hit yes to add liq to "
        f"address :```{is_address}```"
        f"liq to add :```{liq_to_add}```"
    )
    await context.bot.send_message(
        update.effective_chat.id, text, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return WAIT_FOR_ETH_TO_ADD


async def add_liq(update: Update, context: CallbackContext):
    midway = MidWay(update.effective_user.id)
    token_address = context.user_data["token_address"]
    liq_to_add = context.user_data["liq_to_add"]
    txn_hash = await midway.add_liquidity(token_address, liq_to_add)
    confirmed_txn = await midway.wait_for_txn_hash(txn_hash)
    if not txn_hash:
        await context.bot.send_message(
            update.effective_user.id, "Faild to add liquidity to token"
        )
        return ConversationHandler.END

    text = "Liq added to token" "Txn Hash" f"```{txn_hash}```"
    await context.bot.send_message(
        update.effective_chat.id, text, parse_mode="Markdown"
    )
    event_logs: TokenLiqAdded = await midway.event_logs_for_adding_liquidity(
        confirmed_txn
    )
    if not event_logs:
        await context.bot.send_message(
            update.effective_user.id, "Faild to add liquidity to token"
        )
        return ConversationHandler.END
    last_message = (
        "Token Address :"
        f"```{event_logs.token}```"
        "Token Amount :"
        f"```{event_logs.token_added}```"
        "ETH added"
        f"```{event_logs.WETH_added}```"
    )
    await context.bot.send_message(
        update.effective_user.id, last_message, parse_mode="Markdown"
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


add_liq_convo_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(get_token_address, "ADD_LIQ")],
    states={
        WAIT_FOR_TOKEN_ADDRESS: [
            CallbackQueryHandler(stop, "menu"),
            CommandHandler("stop", stop),
            MessageHandler(filters.TEXT & ~filters.COMMAND, prompt_liq_to_add),
        ],
        WAIT_FOR_ETH_TO_ADD: [
            CallbackQueryHandler(stop, "menu"),
            CommandHandler("stop", stop),
            CallbackQueryHandler(add_liq, "yes_add_liq"),
            CallbackQueryHandler(get_token_address, "back"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(random_response, ".*"),
        MessageHandler(filters.ALL, random_response),
    ],
)
