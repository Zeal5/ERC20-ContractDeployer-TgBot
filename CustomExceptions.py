from typing import Optional
from telegram.ext import CallbackContext

class UnknownUserCallData(Exception):
    """ Raised When update.callback_query.data is none
    message : str | Something went wrong Please try again later
    context : CallbackContext | None
    chat_id : user chat id where to send message"""
    def __init__(self, message:Optional[str] = None, context:Optional[CallbackContext] = None, chat_id : Optional[int] = None):
        self.message = message
        self.context = context
        self.chat_id = chat_id

    async def CallDataIsNone(self):
        """ return something went wrong"""
        if self.message is not None:
            await self.context.bot.send_message(self.chat_id, self.message)
        elif self.chat_id is not None:
            await self.context.bot.send_message(self.chat_id,"Something went wrong Please try again later")
        else:
            print("context and chat_id were None")
