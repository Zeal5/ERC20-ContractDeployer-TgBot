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
SHOW_MENU_BUTTONS, GENERATE_WALLET, DEPLOY_TOKEN1, DEPLOY_TOKEN2 = range(4)

async def generate_wallet(update: Update, context: CallbackContext) -> int:
    pass

async def deploy_token2(update: Update, context: CallbackContext) -> int:
    pass

async def deploy_token1(update: Update, context: CallbackContext) -> int:



async def menu_button_clicked(update: Update, context: CallbackContext) -> int:
    """Handles menu button is click
    3 call back data can be returned by menu
        generate_wallet -> Create Wallet
        deploy_token1   -> Deploy Token1
        deploy_token2   -> Deploy Token2
    """
    query = update.callback_query.data
    query = None
    try:
        if query is not None:
            match query:
            #     case "generate_wallet":
            #         return GENERATE_WALLET
                case "deploy_token1":
                    return DEPLOY_TOKEN1
                case "deploy_token2":
                    return DEPLOY_TOKEN2
        else:
            raise UnknownUserCallData(context = context,
                                      chat_id = update.effective_chat.id) 
    except UnknownUserCallData as e:
        await e.CallDataIsNone()

    # ConversationHandler.END


async def enter_main_menu(update: Update, context: CallbackContext) -> int:
    # Create the two buttons
    print("in enter wallet manager")
    button1 = InlineKeyboardButton("Generate Wallet", callback_data="generate_wallet")
    button2 = InlineKeyboardButton("Deploy token1", callback_data="deploy_token1")
    button3 = InlineKeyboardButton("Deploy token2", callback_data="deploy_token2")

    # Combine the two buttons in a single row, each list represents a new row
    keyboard = [
        [
            button1,
        ],
        [
            button2,
            button3,
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    wallet_menu_buttons = await context.bot.send_message(
        update.effective_chat.id, "MENU", reply_markup=reply_markup
    )
    context.user_data["wallet_menu_buttons"] = wallet_menu_buttons.id
    return SHOW_MENU_BUTTONS


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


menu_convo_handler = ConversationHandler(
    entry_points=[
        CommandHandler("menu", enter_main_menu),
        # CallbackQueryHandler(enter_main_menu, pattern="wallet_manager"),
    ],
    states={
        SHOW_MENU_BUTTONS: [CallbackQueryHandler(menu_button_clicked)],
        # ADD_SECRET: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_keys)],
        # EDIT_BUTTONS: [CallbackQueryHandler(editing_wallets)],
    },
    fallbacks=[
        MessageHandler(None, fall_back),
    ],
    allow_reentry=True,
    # per_chat=True,
    # per_user=True,
    # per_message=True,
)
