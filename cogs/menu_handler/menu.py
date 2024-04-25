import os, sys

parent_dir = os.path.dirname(__file__)
sys.path.append(parent_dir)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from CustomExceptions import UnknownUserCallData
from GenerateWallet.delete_wallet import (
    delete_wallet_convo_handler,
    enter_delete_wallet,
)
from TransferTokens.transfer import transfer_tokens_convo_handler
from GenerateWallet.generate_wallet import get_wallet_info
from cogs import (
    RESTART,
    SHOW_MENU_BUTTONS,
    GET_TOKEN_ARGS,
    TRANSFER_FUNDS,
    DEL_WALLET,
)
from DeployToken.deploy_token import deployer_convo_handler


async def enter_main_menu(update: Update, context: CallbackContext) -> int:

    # Create the two buttons
    print("in enter wallet manager")
    button1 = InlineKeyboardButton("Wallet", callback_data="generate_wallet")
    button2 = InlineKeyboardButton("Delete Wallet", callback_data="delete_wallet")
    button3 = InlineKeyboardButton("Deploy token", callback_data="deploy_token1")
    button4 = InlineKeyboardButton("Transfer Funds", callback_data="transfer_funds")

    # Combine the two buttons in a single row, each list represents a new row
    keyboard = [
        [button1, button2],
        [
            button3,
        ],
        [button4],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        query = update.callback_query.data
        if query is not None:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text="THIS IS THE MENU PLEASE PRESS A BUTTON BELOW",
                reply_markup=reply_markup,
            )
            return SHOW_MENU_BUTTONS
    except Exception as e:
        pass
    wallet_menu_buttons = await context.bot.send_message(
        update.effective_chat.id,
        "THIS IS THE MENU PLEASE PRESS A BUTTON BELOW",
        reply_markup=reply_markup,
    )
    context.user_data["wallet_menu_buttons"] = wallet_menu_buttons.id
    return SHOW_MENU_BUTTONS


async def menu_button_clicked(update: Update, context: CallbackContext) -> int:
    """Handles menu button is click
    3 call back data can be returned by menu
        generate_wallet -> Create Wallet
        deploy_token1   -> Deploy Token1
        deploy_token2   -> Deploy Token2
    """
    query = update.callback_query.data
    button = InlineKeyboardButton("MENU", callback_data="menu")
    keyboard = [[button]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = (
        "*Reply to this text with token name,ticker and supply."
        "Each seperated by space\nbitcoin BTC 2100000*"
        "This will create token bitcoin with ticker BTC and 21million supply"
    )
    try:
        if query is not None:
            match query:
                case "generate_wallet":
                    await get_wallet_info(update, context)

                case "deploy_token1":
                    await update.callback_query.answer()
                    await update.callback_query.edit_message_text(
                        text=message, parse_mode="Markdown", reply_markup=reply_markup
                    )
                    return GET_TOKEN_ARGS
                case "transfer_funds":
                    return ConversationHandler.END
                case "delete_wallet":
                    return await enter_delete_wallet(update, context)
                    # await start_wallet_delete_process()
        else:
            raise UnknownUserCallData(context=context, chat_id=update.effective_chat.id)
    except UnknownUserCallData as e:
        await e.CallDataIsNone()


async def fall_back(update: Update, context: CallbackContext):
    print("wallet manager fallback")
    command = update.message.text[1:]
    print(update.message.text)
    if command == "manage_wallets":
        return await enter_main_menu(update, context)
        # return ConversationHandler.END
    print("ending wallet manager convo")
    return ConversationHandler.END


async def stop(update: Update, context: CallbackContext):
    text = "Stoping " "enter `/menu` to goto menu"
    await update.message.reply_text(text=text)
    return ConversationHandler.END


async def restart(update: Update, context: CallbackContext):
    print("restarting")
    # await enter_main_menu(update,context)
    text = "Stoping... " "enter `/menu` to goto menu"
    _query = update.callback_query.data
    print(_query)
    match _query:
        case "yes_goto_menu":
            # await context.bot.send_message(update.effective_chat.id, text)
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text)
            return ConversationHandler.END
    return RESTART


menu_convo_handler = ConversationHandler(
    entry_points=[
        CommandHandler("menu", enter_main_menu),
        CallbackQueryHandler(enter_main_menu, pattern="menu"),
    ],
    states={
        RESTART: [CallbackQueryHandler(restart)],
        SHOW_MENU_BUTTONS: [CallbackQueryHandler(menu_button_clicked)],
        DEL_WALLET: [delete_wallet_convo_handler],
        TRANSFER_FUNDS: [transfer_tokens_convo_handler],
        GET_TOKEN_ARGS: [deployer_convo_handler],
    },
    fallbacks=[CommandHandler("stop", stop)],
    allow_reentry=True,
)
