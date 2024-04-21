from telegram import Update,InlineKeyboardMarkup,InlineKeyboardButton


from telegram.ext import (
    CallbackContext,
)

from CustomExceptions import UnknownUserCallData, SomethingWentWrongWhileCreatingUser

from DeployToken.deployer import check_wallet_balance
from cogs.DataBase.wallet_manager import add_user_and_wallet, UserInfo


async def get_user_info(update: Update, context: CallbackContext):
    # check user exists
    """
    user_exists = await check_user_exists(update.effective_user.id)

    # if user exists return user id, wallet addr
    if isinstance(user_exists,UserInfo):
        return user_exists
    """

    # if user doens't exists create user and return id and wallet
    return await add_user_and_wallet(update.effective_user.id)


async def handle_wallet_generation(update: Update, context: CallbackContext):
    try:
        user_info = await get_user_info(update, context)
        print(user_info)
        if not isinstance(user_info, UserInfo):
            raise SomethingWentWrongWhileCreatingUser(
                context=context, chat_id=update.effective_chat.id
            )
        _balance = await check_wallet_balance(user_info.address)
        message = (
            f"Wallet Address :"
            "\n"
            f"`{user_info.address}`"
            "\n"
            "Wallet Balance :"
            f"`{_balance}`"
        )
        # get user wallet balance
        button1 = InlineKeyboardButton("MENU", callback_data="menu")
        keyboard = [[button1]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=message, reply_markup=reply_markup, parse_mode="Markdown"
        )
        return
    except SomethingWentWrongWhileCreatingUser as e:
        print(f"raised an erro while creating user {str(e)}")
        await e.UserNotCreated()
    except Exception as e:
        print(str(e))
        print(f"Something went wrong in handle wallet generation {str(e)}")
    await context.bot.send_message(
        update.effective_chat.id, "Failed to get Wallet Balance", parse_mode="Markdown"
    )


async def get_wallet_info(update: Update, context: CallbackContext):
    await handle_wallet_generation(update, context)
