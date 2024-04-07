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

from CustomExceptions import UnknownUserCallData, SomethingWentWrongWhileCreatingUser
from cogs.menu_handler.deploy_tokens import AsyncDeployer
from cogs.menu_handler.generate_wallet import get_wallet_info


@dataclass
class Token:
    name: str
    symbol: str
    supply: int

@dataclass
class TokenInfo:
    buy_tax:int
    sell_tax:int
    owner_address : str

(
    SHOW_MENU_BUTTONS,
    GENERATE_WALLET,
    GET_TOKEN_ARGS,
    DEPLOY_TOKEN1,
    START_DEPLOYMENT,
    LOW_GAS_FEE,
    ADD_LIQ,
) = range(7)


def clean_token_args(_args: str) -> Optional[Token]:
    try:
        name, ticker, supply = _args.strip().split()
        return Token(name, ticker, int(supply))
    except Exception as e:
        return None


async def start_deployment(update: Update, context: CallbackContext):
    # check query selected by user
    print("in start deployment")
    query = update.callback_query.data
    try:
        if query is not None:
            await context.bot.delete_message(
                update.effective_chat.id, context.user_data["deployment_confirmation"]
            )
            match query:
                case "yes":
                    # start deployment
                    _deployer = context.user_data["deployer"]
                    # try:
                    token_deployment_hash = await _deployer.deploy()
                    # Send token deployment hash to user
                    await context.bot.send_message(
                        update.effective_chat.id, f"{token_deployment_hash}"
                    )

                    # On successful token launch send token args
                    txn_hash = await _deployer.wait_for_tx_hash(
                        token_deployment_hash
                    )
                    logs = await _deployer.wait_for_event_logs(txn_hash)
                    # if not logs:
                    #     raise Exception()
                    # TokenInfo => send token address,name,symbol,owner,taxes,
                    context.user_data["token_address"] = logs.token_address
                    _token_params_message = f"Token deployed successfuly with\nAddress: `{logs.token_address}`\nPool: `{logs.pool_address}`\nname: {logs.name}\nsymbol: {logs.symbol}\nowner: `{logs.owner}`\nbuy tax: {logs.buyTax}%\nsell tax: {logs.sellTax}%"
                    await context.bot.send_message(
                        update.effective_chat.id,
                        _token_params_message,
                        parse_mode="Markdown",
                    )
                    # @DEV
                    await add_liq_clicked(update, context)
                case "no":
                    print("selected no ")
                    await context.bot.send_message(
                        update.effective_chat.id,
                        "Selected No\nSend `/menu` to start again",
                        parse_mode="Markdown",
                    )
                    ConversationHandler.END
        else:
            raise UnknownUserCallData(context=context, chat_id=update.effective_chat.id)


    except UnknownUserCallData as e:
        await e.CallDataIsNone()

    except Exception as e:
        # Raise error
        print(f"error in Deploy token1 {str(e)}")
        await context.bot.send_message(
            update.effective_chat.id, "Couldn't deploy token"
        )

        ConversationHandler.END




async def prompt_low_gas_fee(update: Update, context: CallbackContext):
    deployer = context.user_data["deployer"]
    await deployer.get_account()

    # Prompt user for confirmation of gas fee get gas fee
    gas_fee = await deployer.estimate_gas(True)
    wallet_balance = await deployer.check_wallet_balance()
    print("required gas fee")
    print(gas_fee)
    if gas_fee > (wallet_balance * 10**18):
        await context.bot.send_message(
            update.effective_chat.id,
            f"Low Balance.Reload balance and reply to this message to continue\n`{deployer.address}`",
            parse_mode="Markdown",
        )
        return LOW_GAS_FEE
    await pre_deployment_prompt(update, context, gas_fee)
    return START_DEPLOYMENT

def  clean_token_tax_info(_info : str):
    try:
        buy_tax, sell_tax, owner = _info.strip().split()
        if not owner.startswith('0x') or  len(owner) != 42:
            return False

        return TokenInfo(
                int(buy_tax),
                int(sell_tax),
                str(owner))
    except Exception as e:
        print(f"exception in cleaning tax info {str(e)}")
        return None

async def deploy_token(update: Update, context: CallbackContext):
    _reply = update.message.text
    clean_tax_info = clean_token_tax_info(_reply)
    print(clean_tax_info)
    if not isinstance(clean_tax_info,TokenInfo):
        await update.message.reply_text("Invalid Input")
        return DEPLOY_TOKEN1
    # Check wallet balance is gt cost of deployment and liq
    buy_tax = clean_tax_info.buy_tax
    sell_tax = clean_tax_info.sell_tax
    owner_tax_share = 90
    owner_addr = clean_tax_info.owner_address
    basu_funds_addr = "0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f"

    _token = context.user_data['token_info']
    deployer = AsyncDeployer(
        update.effective_user.id,
        supply=_token.supply,
        name=_token.name,
        symbol=_token.symbol,
        buy_tax=buy_tax,
        sell_tax=sell_tax,
        owner_tax_share=owner_tax_share,
        owner_tax_address=owner_addr,
        basu_tax_address=basu_funds_addr,
    )
    print("deployer initiated")
    context.user_data["deployer"] = deployer
    await deployer.get_account()

    # Prompt user for confirmation of gas fee get gas fee
    """
    gas_fee = await deployer.estimate_gas(True)
    wallet_balance = await deployer.check_wallet_balance()
    print("required gas fee")
    print(gas_fee)
    if gas_fee > (wallet_balance * 10**18):
        await context.bot.send_message(
            update.effective_chat.id,
            f"Low Balance.Reload balance and reply to this message to continue\n`{deployer.address}`",
            parse_mode="Markdown",
        )
        return LOW_GAS_FEE
    await pre_deployment_prompt(update, context, gas_fee)
    """
    await pre_deployment_prompt(update, context, 2.1)
    return START_DEPLOYMENT



async def get_token_args(update: Update, context: CallbackContext):
    _reply = update.message.text
    # Clean args
    _token = clean_token_args(_reply)
    if not isinstance(_token, Token):
        await update.message.reply_text("Invalid Input")
        return GET_TOKEN_ARGS

    context.user_data['token_info'] = _token
    # get taxes and owner address
    await context.bot.send_message(
    update.effective_chat.id, "Enter BUY tax Sell tax and owner address.\nSeperated by space"
    )
    return DEPLOY_TOKEN1


async def pre_deployment_prompt(update: Update, context: CallbackContext, gas_fee):
    button1 = InlineKeyboardButton("YES", callback_data="yes")
    button2 = InlineKeyboardButton("NO", callback_data="no")
    keyboard = [[button1, button2]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    deployment_confirmation_button = await context.bot.send_message(
        update.effective_chat.id,
        f"*Are you sure you want to procced*\nTotal gas cost will be {float(gas_fee):5f} ETH",
        reply_markup=reply_markup,
    )
    context.user_data["deployment_confirmation"] = deployment_confirmation_button.id


async def add_liq_clicked(update: Update, context: CallbackQueryHandler):
    # Show total cost
    # Add liq
    _deployer = context.user_data["deployer"]
    wait_liq_adding_message = await context.bot.send_message(
        update.effective_chat.id, "ETH to add to liq", parse_mode="Markdown"
    )



    txn_hash = await _deployer.add_liquidity(context.user_data["token_address"], 0.2)
    await context.bot.delete_message(update.effective_chat.id, wait_liq_adding_message.id)
    await context.bot.send_message(
        update.effective_chat.id, txn_hash, parse_mode="Markdown"
    )
    txn = await _deployer.wait_for_tx_hash(txn_hash)
    logs = await _deployer.event_logs_for_adding_liquidity(txn)
    log_message = (
        f"{logs.token}\ntoken Added: {logs.token_added}\nweth added : {logs.WETH_added}"
    )
    await context.bot.send_message(
        update.effective_chat.id, log_message, parse_mode="Markdown"
    )


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
                    await get_wallet_info(update, context)

                case "deploy_token1":
                    await context.bot.send_message(
                        update.effective_chat.id, message, parse_mode="Markdown"
                    )
                    return GET_TOKEN_ARGS

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

    # Combine the two buttons in a single row, each list represents a new row
    keyboard = [
        [
            button1,
        ],
        [
            button2,
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
        GET_TOKEN_ARGS: [MessageHandler(filters.TEXT,get_token_args)],
        DEPLOY_TOKEN1: [MessageHandler(filters.TEXT,deploy_token)],
        START_DEPLOYMENT: [CallbackQueryHandler(start_deployment)],
        LOW_GAS_FEE: [MessageHandler(filters.TEXT, prompt_low_gas_fee)],
    },
    fallbacks=[
        MessageHandler(None, fall_back),
    ],
    allow_reentry=True,
    # per_chat=True,
    # per_user=True,
    # per_message=True,
)
