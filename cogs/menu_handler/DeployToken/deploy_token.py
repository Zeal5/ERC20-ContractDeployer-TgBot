from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from time import time
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
)
from dataclasses import dataclass
from typing import Optional
from CustomExceptions import UnknownUserCallData
from .deployer import AsyncDeployer
from .helpers import clean_token_args,clean_token_tax_info
from . import TokenArgs,Token
(
    SHOW_MENU_BUTTONS,
    GET_TOKEN_ARGS,
    DEPLOY_TOKEN1,
    START_DEPLOYMENT,
    LOW_GAS_FEE,
    ADD_LIQ,
    LOCK_LIQ,
    DEL_WALLET,
    GENERATE_NEW_WALLET
) = range(9)

from dataclasses import dataclass


async def get_token_args(update: Update, context: CallbackContext):
    _reply = update.message.text
    # Clean args
    _token = clean_token_args(_reply)
    if not isinstance(_token, Token):
        await update.message.reply_text("Invalid Input")
        return GET_TOKEN_ARGS

    context.user_data["token_info"] = _token
    # get taxes and owner address
    await context.bot.send_message(
        update.effective_chat.id,
        "Enter BUY tax Sell tax and owner address.\nSeperated by space",
    )
    return DEPLOY_TOKEN1

async def deploy_token(update: Update, context: CallbackContext):
    _reply = update.message.text
    clean_tax_info = clean_token_tax_info(_reply)
    print(clean_tax_info)
    if not isinstance(clean_tax_info, TokenArgs):
        await update.message.reply_text("Invalid Input")
        return DEPLOY_TOKEN1
    # Check wallet balance is gt cost of deployment and liq
    buy_tax = clean_tax_info.buy_tax
    sell_tax = clean_tax_info.sell_tax
    owner_tax_share = 90
    owner_addr = clean_tax_info.owner_address
    basu_funds_addr = "0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f"

    _token = context.user_data["token_info"]
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
    # @DEV if no account found uncomment
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
                    txn_hash = await _deployer.wait_for_tx_hash(token_deployment_hash)
                    logs = await _deployer.wait_for_event_logs(txn_hash)
                    # if not logs:
                    #     raise Exception()
                    # TokenArgs => send token address,name,symbol,owner,taxes,
                    context.user_data["token_address"] = logs.token_address
                    _token_params_message = f"Token deployed successfuly with\nAddress: `{logs.token_address}`\nPool: `{logs.pool_address}`\nname: {logs.name}\nsymbol: {logs.symbol}\nowner: `{logs.owner}`\nbuy tax: {logs.buyTax}%\nsell tax: {logs.sellTax}%"
                    await context.bot.send_message(
                        update.effective_chat.id,
                        _token_params_message,
                        parse_mode="Markdown",
                    )
                    # @DEV
                    await context.bot.send_message(
                        update.effective_chat.id,
                        "How much ETH to add to liq",
                        parse_mode="Markdown",
                    )
                    return ADD_LIQ
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


async def add_liq_clicked(update: Update, context: CallbackQueryHandler):
    # Show total cost
    # Add liq
    liq_value = update.message.text
    try:
        liq_value = float(liq_value.strip())
    except Exception as e:
        print(f"error while parsing liq value {str(e)}")
        await context.bot.send_message(
            update.effective_chat.id,
            "Wrong Valu: How much ETH to add to liq",
            parse_mode="Markdown",
        )
        return ADD_LIQ
    _deployer = context.user_data["deployer"]

    txn_hash = await _deployer.add_liquidity(
        context.user_data["token_address"], liq_value
    )
    if txn_hash is None:
        await context.bot.send_message(
            update.effective_chat.id,
            "Failed to add liq to token",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

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
    # Lock liquidity
    await prompt_lock_duration(update, context)
    return LOCK_LIQ


async def prompt_lock_duration(update: Update, context: CallbackContext):
    button1 = InlineKeyboardButton("1 WEEK", callback_data="1week")
    button2 = InlineKeyboardButton("15 DAYS", callback_data="15days")
    button3 = InlineKeyboardButton("1 MONTH", callback_data="1month")
    button4 = InlineKeyboardButton("1 YEAR", callback_data="1year")

    # Combine the two buttons in a single row, each list represents a new row
    keyboard = [
        [button1, button2],
        [button3, button4],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    wallet_menu_buttons = await context.bot.send_message(
        update.effective_chat.id, "SELECT LOCK DURATION", reply_markup=reply_markup
    )
    context.user_data["lock_duration"] = wallet_menu_buttons.id


async def lock_liq_function(update: Update, context: CallbackContext):
    await context.bot.delete_message(
        update.effective_chat.id, context.user_data["lock_duration"]
    )
    query = update.callback_query.data
    duration = 0
    if query is not None:
        match query:
            case '1week':
                duration = int(time()) + (7 * 24 * 60 * 60)
            case '15days':
                duration = int(time()) + (15 * 24 * 60 * 60)
            case '1month':
                duration = int(time()) + (30 * 24 * 60 * 60)
            case '1year':
                duration = int(time()) + (367 * 24 * 60 * 60)
    print(f"duration to lock {duration}")
    _deployer = context.user_data["deployer"]
    _token_address = context.user_data["token_address"]
    hash = await _deployer.lock_tokens(_token_address,duration)
    await context.bot.send_message(update.effective_chat.id, f"LIQ lock hash\n{hash}")
