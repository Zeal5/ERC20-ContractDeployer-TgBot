from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from dataclasses import dataclass
from typing import Optional

from CustomExceptions import UnknownUserCallData
from .deploy_tokens import AsyncDeployer


@dataclass
class Token:
    name: str
    symbol: str
    supply: int


SHOW_MENU_BUTTONS, GENERATE_WALLET, DEPLOY_TOKEN1, DEPLOY_TOKEN2 = range(4)


async def generate_wallet(update: Update, context: CallbackContext) -> int:
    pass


async def deploy_token2(update: Update, context: CallbackContext) -> int:
    pass


def clean_token_args(_args: str) -> Optional[Token]:
    try:
        name, ticker, supply = _args.strip().split()
        return Token(name, ticker, int(supply))
    except Exception as e:
        return None


async def deploy_token1(update: Update, context: CallbackContext):
    _reply = update.message.text
    # Clean args
    _token = clean_token_args(_reply)
    if not isinstance(_token, Token):
        await update.message.reply_text("Invalid Input")
        return DEPLOY_TOKEN1
    # pass args to deploy()
    buy_tax = 4
    sell_tax = 5
    owner_tax_share = 80
    owner_addr = "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720"
    basu_funds_addr = "0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f"
    _deployer = AsyncDeployer()
    deployment_hash = await  _deployer.deploy(
        supply=_token.supply,
        name=_token.name,
        symbol=_token.symbol,
        buy_tax=buy_tax,
        sell_tax=sell_tax,
        owner_tax_share=owner_tax_share,
        owner_tax_address=owner_addr,
        basu_tax_address=basu_funds_addr,
    )
    # return hash
    await context.bot.send_message(update.effective_chat.id,"ok")
    # return success
    txn_receipt = await _deployer.wait_for_tx_hash(deployment_hash)
    txn_receipt_message = "Contract Address "
    await update.message.reply_text("finished")
    ConversationHandler.END


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
            await context.bot.delete_message(
                update.effective_chat.id, context.user_data["wallet_menu_buttons"]
            )
            match query:
                case "generate_wallet":
                    return GENERATE_WALLET

                case "deploy_token1":
                    await context.bot.send_message(
                        update.effective_chat.id, message, parse_mode="Markdown"
                    )
                    return DEPLOY_TOKEN1

                case "deploy_token2":
                    await context.bot.send_message(
                        update.effective_chat.id, message, parse_mode="Markdown"
                    )
                    return DEPLOY_TOKEN2
        else:
            raise UnknownUserCallData(context=context, chat_id=update.effective_chat.id)
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
        DEPLOY_TOKEN1: [MessageHandler(filters.TEXT, deploy_token1)],
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
