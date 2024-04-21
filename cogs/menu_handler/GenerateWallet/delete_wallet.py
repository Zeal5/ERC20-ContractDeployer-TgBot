from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
)

from CustomExceptions import UnknownUserCallData, SomethingWentWrongWhileCreatingUser
from typing import Union
from DeployToken.deployer import check_wallet_balance
from DeployToken.deploy_token import DEL_WALLET, GENERATE_NEW_WALLET
from cogs.DataBase.wallet_manager import (
    delete_user,
    add_user_and_wallet,
    _check_user_exists,
)
from cogs.DataBase import UserInfo


async def enter_delete_wallet(update: Update, context: CallbackContext):
    # get user address
    user: Union[UserInfo, bool] = await _check_user_exists(update.effective_user.id)
    button1 = InlineKeyboardButton("Back", callback_data="menu")
    if not user:
        wallet_info = await add_user_and_wallet(update.effective_user.id)

        # reply to user a new account has been created
        await update.callback_query.answer()
        text = (
            "New Wallet has been created Successfully"
            "\n"
            "Address :\n"
            f"`{wallet_info.address}`"
            "\n"
            "Secret :\n"
            f"`{wallet_info.secret}`"
        )
        reply_markup = InlineKeyboardMarkup([[button1]])
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )
        return

    # get user balance
    balance = await check_wallet_balance(user.address)
    text = (
        "Are you sure you want to delete your old wallet?"
        f"Your wallet balance is {balance:.4f}"
    )
    # prompt user for confirmation
    button2 = InlineKeyboardButton("Delete Wallet", callback_data="del")
    keyboard = [[button2], [button1]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    return DEL_WALLET


async def delete_wallet(update: Update, context: CallbackContext):
    user_deleted = await delete_user(update.effective_user.id)
    if not user_deleted:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text="Something Went wrong")
        return ConversationHandler.END

    text = "Wallet has been deleted"
    button1 = InlineKeyboardButton("MENU", callback_data="menu")
    button2 = InlineKeyboardButton(
        "Get New Wallet", callback_data="GENERATE_NEW_WALLET"
    )
    keyboard = [[button2], [button1]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    return GENERATE_NEW_WALLET


async def gen_new_wallet(update: Update, context: CallbackContext):
    button1 = InlineKeyboardButton("Back", callback_data="menu")
    wallet_info = await add_user_and_wallet(update.effective_user.id)

    # reply to user a new account has been created
    await update.callback_query.answer()
    text = (
        "New Wallet has been created Successfully"
        "\n"
        "Address :\n"
        f"`{wallet_info.address}`"
        "\n"
        "Secret :\n"
        f"`{wallet_info.secret}`"
    )
    reply_markup = InlineKeyboardMarkup([[button1]])
    await update.callback_query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )
    return


async def stop(update: Update, context: CallbackContext):
    text = "Stoping " "enter `/menu` to goto menu"
    await update.message.reply_text(text=text)
    return ConversationHandler.END


delete_wallet_convo_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(delete_wallet, pattern="del")],
    states={GENERATE_NEW_WALLET: [CallbackQueryHandler(gen_new_wallet)]},
    fallbacks=[CommandHandler("stop", stop)],
)
