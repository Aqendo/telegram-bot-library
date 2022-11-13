from enum import Enum
from typing import Union


def convert_dict(d: dict, typeof: str):
    if typeof == "message":
        return Message(
            message_id=d["message_id"],
            date=d["date"],
            chat=convert_dict(d["chat"], "chat"),
            message_thread_id=d["message_thread_id"] if "message_thread_id" in d else None,
            from_user=d["from"] if "from" in d else None,
            sender_chat=convert_dict(d["sender_chat"], "chat") if "sender_chat" in d else None,
            forward_from=d["forward_from"] if "forward_from" in d else None,
            forward_from_chat=d["forward_from_chat"] if "forward_from_chat" in d else None,
            forward_from_message_id=d["forward_from_message_id"] if "forward_from_message_id" in d else None,
            reply_to_message=d["reply_to_message"] if "reply_to_message" in d else None,
            via_bot=d["via_bot"] if "via_bot" in d else None,
            text=d["text"] if "text" in d else None,
            reply_markup=d["reply_markup"] if "reply_markup" in d else None,
        )
    elif typeof == "chat":
        return Chat(
            id=d["id"],
            typeof=d["type"],
            title=d["title"] if "title" in d else None,
            username=d["username"] if "username" in d else None,
            first_name=d["first_name"] if "first_name" in d else None,
            last_name=d["last_name"] if "last_name" in d else None
        )
    elif typeof == "callback_query":
        return CallbackQuery(
            id=d["id"],
            from_user=d["from"],  # class User
            chat_instance=d["chat_instance"],
            message=convert_dict(d["message"], "message") if "message" in d else None,
            inline_message_id=d["inline_message_id"] if "inline_message_id" in d else None,
            data=d["data"] if "data" in d else None,
            game_short_name=d["game_short_name"] if "game_short_name" in d else None,
        )
    return d


class Handlers():
    onMessage = "onMessage"
    onEditedMessage = "onEditedMessage"
    onEditedChannelPost = "onEditedChannelPost"
    onChannelPost = "onChannelPost"
    onMessageOnly = "onMessageOnly"
    onInlineQuery = "onInlineQuery"
    onChosenInlineResult = "onChosenInlineResult"
    onCallbackQuery = "onCallbackQuery"
    onShippingQuery = "onShippingQuery"
    onPreCheckoutQuery = "onPreCheckoutQuery"
    onPoll = "onPoll"
    onPollAnswer = "onPollAnswer"
    onChatMemberUpdated = "onChatMemberUpdated"
    onChatJoinRequest = "onChatJoinRequest"


# TYPES OF TELEGRAM OBJECTS

class BaseType:
    def __repr__(self):
        fields = tuple("{}={}".format(k, v) for k, v in self.__dict__.items())
        return self.__class__.__name__ + str(tuple(sorted(fields))).replace("\'", "")


class Chat(BaseType):
    def __init__(
            self,
            id: int,
            typeof: str,
            title: Union[str, None] = None,
            username: Union[str, None] = None,
            first_name: Union[str, None] = None,
            last_name: Union[str, None] = None
    ):
        self.id = id
        self.type = typeof,
        self.title = title
        self.username = username
        self.first_name = first_name
        self.last_name = last_name


class Message(BaseType):
    def __init__(
            self,
            message_id: int,
            date: int,
            chat: Chat,
            message_thread_id: Union[int, None] = None,
            from_user: Union[dict, None] = None,
            sender_chat: Union[Chat, None] = None,
            forward_from: Union[dict, None] = None,
            forward_from_chat: Union[dict, None] = None,
            forward_from_message_id: Union[int, None] = None,
            reply_to_message: Union[dict, None] = None,
            via_bot: Union[dict, None] = None,
            text: Union[str, None] = None,
            reply_markup: Union[dict, None] = None
    ):
        self.message_id = message_id
        self.date = date
        self.chat = chat
        self.message_thread_id = message_thread_id
        self.from_user = from_user
        self.sender_chat = sender_chat
        self.forward_from = forward_from
        self.forward_from_chat = forward_from_chat
        self.forward_from_message_id = forward_from_message_id
        self.reply_to_message = reply_to_message
        self.via_bot = via_bot
        self.text = text
        self.reply_markup = reply_markup


class CallbackQuery(BaseType):
    def __init__(
            self,
            id: str,
            from_user: dict, # class User
            chat_instance: str,
            message: Union[Message, None] = None,
            inline_message_id: Union[str, None] = None,
            data: Union[str, None] = None,
            game_short_name: Union[str, None] = None
    ):
        self.id = id
        self.from_user = from_user
        self.chat_instance = chat_instance
        self.message = message
        self.inline_message_id = inline_message_id
        self.data = data
        self.game_short_name = game_short_name