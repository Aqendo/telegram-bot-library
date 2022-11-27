from enum import Enum
from typing import Union

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

def convert_dict(d: dict, typeof: str):
    if typeof == "message":
        return Message(
            message_id=d["message_id"],
            date=d["date"],
            chat=convert_dict(d["chat"], "chat"),
            message_thread_id=d["message_thread_id"] if "message_thread_id" in d else None,
            from_user=convert_dict(d["from"], "user") if "from" in d else None,
            sender_chat=convert_dict(d["sender_chat"], "chat") if "sender_chat" in d else None,
            forward_from=convert_dict(d["forward_from"], "user") if "forward_from" in d else None,
            forward_from_chat=d["forward_from_chat"] if "forward_from_chat" in d else None,
            forward_from_message_id=d["forward_from_message_id"] if "forward_from_message_id" in d else None,
            reply_to_message=d["reply_to_message"] if "reply_to_message" in d else None,
            via_bot=convert_dict(d["via_bot"], "user") if "via_bot" in d else None,
            text=d["text"] if "text" in d else None,
            reply_markup=d["reply_markup"] if "reply_markup" in d else None,
            entities=d["entities"] if "entities" in d else None
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
            from_user=convert_dict(d["from"], "user"),  # class User
            chat_instance=d["chat_instance"],
            message=convert_dict(d["message"], "message") if "message" in d else None,
            inline_message_id=d["inline_message_id"] if "inline_message_id" in d else None,
            data=d["data"] if "data" in d else None,
            game_short_name=d["game_short_name"] if "game_short_name" in d else None,
        )
    elif typeof == "user":
        return User(
            id=d["id"],
            is_bot=d["is_bot"],
            first_name=d["first_name"] if "first_name" in d else None,
            last_name=d["last_name"] if "last_name" in d else None,
            username=d["username"] if "username" in d else None,
            language_code=d["language_code"] if "language_code" in d else None,
            is_premium=d["is_premium"] if "is_premium" in d else None,
            added_to_attachment_menu=d["added_to_attachment_menu"] if "added_to_attachment_menu" in d else None,
            can_join_groups=d["can_join_groups"] if "can_join_groups" in d else None,
            can_read_all_group_messages=d["can_read_all_group_messages"] if "can_read_all_group_messages" in d else None,
            supports_inline_queries=d["supports_inline_queries"] if "supports_inline_queries" in d else None
        )
    return d

class BaseType:
    def __repr__(self):
        fields = tuple("{}={}".format(k, v) for k, v in self.__dict__.items())
        return self.__class__.__name__ + str(tuple(sorted(fields))).replace("\'", "")


class User(BaseType):
    def __init__(
            self,
            id: int,
            is_bot: bool,
            first_name: str,
            last_name: Union[str, None] = None,
            username: Union[str, None] = None,
            language_code: Union[str, None] = None,
            is_premium: Union[bool, None] = None,
            added_to_attachment_menu: Union[bool, None] = None,
            can_join_groups: Union[bool, None] = None,
            can_read_all_group_messages: Union[bool, None] = None,
            supports_inline_queries: Union[bool, None] = None
    ):
        self.id = id
        self.is_bot = is_bot
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.language_code = language_code
        self.is_premium = is_premium
        self.added_to_attachment_menu = added_to_attachment_menu
        self.can_join_groups = can_join_groups
        self.can_read_all_group_messages = can_read_all_group_messages
        self.supports_inline_queries = supports_inline_queries

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
            from_user: Union[User, None] = None,
            sender_chat: Union[Chat, None] = None,
            forward_from: Union[User, None] = None,
            forward_from_chat: Union[dict, None] = None,
            forward_from_message_id: Union[int, None] = None,
            reply_to_message: Union[dict, None] = None,
            via_bot: Union[dict, None] = None,
            text: Union[str, None] = None,
            reply_markup: Union[dict, None] = None,
            entities: Union[list, None] = None
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
        self.entities = entities


class CallbackQuery(BaseType):
    def __init__(
            self,
            id: str,
            from_user: User, # class User
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



