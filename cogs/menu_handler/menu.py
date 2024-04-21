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
import os, sys

parent_dir = os.path.dirname(__file__)
sys.path.append(parent_dir)
print(sys.path)
from GenerateWallet.delete_wallet import delete_wallet_convo_handler, enter_delete_wallet
from GenerateWallet.generate_wallet import get_wallet_info
from DeployToken.deploy_token import (
    get_token_args,
    deploy_token,
    start_deployment,
    prompt_low_gas_fee,
    add_liq_clicked,
    lock_liq_function,
    SHOW_MENU_BUTTONS,
    GET_TOKEN_ARGS,
    DEPLOY_TOKEN1,
    START_DEPLOYMENT,
    LOW_GAS_FEE,
    ADD_LIQ,
    LOCK_LIQ,
    DEL_WALLET,
)


async def enter_main_menu(update: Update, context: CallbackContext) -> int:

    # Create the two buttons
    print("in enter wallet manager")
    button1 = InlineKeyboardButton("Wallet", callback_data="generate_wallet")
    button2 = InlineKeyboardButton("Delete Wallet", callback_data="delete_wallet")
    button3 = InlineKeyboardButton("Deploy token1", callback_data="deploy_token1")

    # Combine the two buttons in a single row, each list represents a new row
    keyboard = [
        [button1, button2],
        [
            button3,
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        query = update.callback_query.data
        if query is not None:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text="THIS IS THE MENU PLEASE PRESS A BUTTON BELOW", reply_markup=reply_markup
            )
            return SHOW_MENU_BUTTONS
    except Exception as e:
        pass
    wallet_menu_buttons = await context.bot.send_message(
        update.effective_chat.id, "THIS IS THE MENU PLEASE PRESS A BUTTON BELOW", reply_markup=reply_markup
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
    message = "*Reply to this text with token name,ticker and supply.\nEach seperated by space\nbitcoin BTC 2100000*\nThis will create token bitcoin with ticker BTC and 21million supply"
    try:
        if query is not None:
            # await context.bot.delete_message(
            #     update.effective_chat.id, context.user_data["wallet_menu_buttons"]
            # )
            match query:
                case "generate_wallet":
                    await get_wallet_info(update, context)

                case "deploy_token1":
                    await context.bot.send_message(
                        update.effective_chat.id, message, parse_mode="Markdown"
                    )
                    return GET_TOKEN_ARGS
                case "delete_wallet":
                    return await enter_delete_wallet(update, context)
                    # await start_wallet_delete_process()
        else:
            raise UnknownUserCallData(context=context, chat_id=update.effective_chat.id)
    except UnknownUserCallData as e:
        await e.CallDataIsNone()
    # ConversationHandler.END


async def fall_back(update: Update, context: CallbackContext):
    # Call the start command handler to show the buttons again
    # await start_command(update, context)
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


menu_convo_handler = ConversationHandler(
    entry_points=[
        CommandHandler("menu", enter_main_menu),
        CallbackQueryHandler(enter_main_menu, pattern="menu"),
    ],
    states={
        SHOW_MENU_BUTTONS: [CallbackQueryHandler(menu_button_clicked)],
        DEL_WALLET: [delete_wallet_convo_handler],
        GET_TOKEN_ARGS: [MessageHandler(filters.TEXT, get_token_args)],
        DEPLOY_TOKEN1: [MessageHandler(filters.TEXT, deploy_token)],
        START_DEPLOYMENT: [CallbackQueryHandler(start_deployment)],
        LOW_GAS_FEE: [MessageHandler(filters.TEXT, prompt_low_gas_fee)],
        ADD_LIQ: [MessageHandler(filters.TEXT, add_liq_clicked)],
        LOCK_LIQ: [CallbackQueryHandler(lock_liq_function)],
    },
    fallbacks=[MessageHandler(None, fall_back), CommandHandler("stop", stop)],
    allow_reentry=True,
)
