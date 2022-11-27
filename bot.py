import aiohttp
import asyncio
import logging
import traceback
import json
from typing import Any, Union, List
from .types import convert_dict


class Poller:
    def __init__(self, token, queue: asyncio.Queue, session, api_url: Union[str, None] = "api.telegram.org", skip_updates: bool = False):
        self.queue = queue
        self.token = token
        self.session = session
        self.api_url = "https://" + api_url + "/bot"
        self.skip_updates = skip_updates

    async def make_request(self, method, data):
        async with self.session.post(self.api_url + self.token + "/" + method, data=data) as post:
            a = await post.json()
            logging.debug(a)
            return a

    async def _worker(self, skip_updates: bool):
        offset = -1
        to_skip = skip_updates
        while True:
            res = await self.make_request("getUpdates", {"offset": offset})
            for i in res['result']:
                offset = i['update_id'] + 1
                if to_skip: continue
                self.queue.put_nowait(i)
            to_skip = False

    async def start(self):
        asyncio.create_task(self._worker(self.skip_updates))


class Worker:
    def __init__(self, token: str, queue: asyncio.Queue, workers_amount: int, session, handle_update):
        self.token = token
        self.queue = queue
        self.workers_amount = workers_amount
        self.session = session
        self.handle_update = handle_update

        # print(update)

    async def _worker(self):
        while True:
            upd = await self.queue.get()
            await self.handle_update(upd)

    async def start(self):
        for _ in range(self.workers_amount):
            asyncio.create_task(self._worker())


class Bot:
    def __init__(self, token: str, n: int, api_url: Union[str, None] = "api.telegram.org", skip_updates: bool = False):
        self.queue = asyncio.Queue()
        if not isinstance(token, str) or len(token) == 0:
            raise ValueError("A valid token must be provided.")
        self.token = token
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(
        #    headers={
        #    'Content-Type': 'application/json'
        #}
        )
        self.poller = Poller(token, self.queue, self.session, skip_updates=skip_updates)
        self.worker = Worker(token, self.queue, n, self.session, self._handle_update)
        self.api_url = "https://" + api_url + "/bot"

    def __del__(self):
        asyncio.run(self.session.close())
        
    # this function is a decorator, that's why it is so strange
    def register(self, method):
        def a(func, preserved=self):
            setattr(preserved, method, getattr(preserved, method) + [func])
            return func
        return a

    def load_module(self, module):
        for i in module.get_funcs():
            self.register(i[1])(i[0])

    def apply_entities(self, text: str, entities: list):
        raise NotImplemented # It doesn't work well for now.
        print("TEXT", text)
        print("ENTITIES", entities)
        for i in entities:
            entity_type = i["type"]
            length = i["length"]
            offset = i["offset"]
            tags = ("","")
            if entity_type == "bold":
                tags = ("<b>", "</b>")
            elif entity_type == "code":
                tags = ("<code>", "</code>")
            text = text[:offset] \
            + tags[0] \
            + text[offset:offset+length] \
            + tags[1] \
            + text[offset+length:]
        return text
    async def _handle_update(self, update: dict):
        try:
            tasks = []
            if "message" in update:
                print(update)
                tasks += [func(convert_dict(update["message"], "message")) for func in self.onMessage]
                tasks += [func(convert_dict(update["message"], "message")) for func in self.onMessageOnly]
            elif "edited_message" in update:
                tasks += [func(convert_dict(update["edited_message"], "message")) for func in self.onMessage]
                tasks += [func(convert_dict(update["edited_message"], "message")) for func in self.onEditedMessage]
            elif "channel_post" in update:
                tasks += [func(convert_dict(update["channel_post"], "message")) for func in self.onMessage]
                tasks += [func(convert_dict(update["channel_post"], "message")) for func in self.onChannelPost]
            elif "edited_channel_post" in update:
                tasks += [func(convert_dict(update["edited_channel_post"], "message")) for func in self.onMessage]
                tasks += [func(convert_dict(update["edited_channel_post"], "message")) for func in self.onEditedChannelPost]
            elif "inline_query" in update:
                tasks += [func(update["inline_query"]) for func in self.onInlineQuery]
            elif "chosen_inline_result" in update:
                tasks += [func(update["chosen_inline_result"]) for func in self.onChosenInlineResult]
            elif "callback_query" in update:
                tasks += [func(convert_dict(update["callback_query"], "callback_query")) for func in self.onCallbackQuery]
            tasks += [func(update) for func in self.onRaw]
            logging.error("Unknown update type: %s" % list(update.keys())[1])
            await asyncio.gather(*tasks)
        except Exception as e:
            traceback.print_exc()

    onMessageOnly = []
    onMessage = []
    onEditedMessage = []
    onEditedChannelPost = []
    onChannelPost = []
    onInlineQuery = []
    onChosenInlineResult = []
    onCallbackQuery = []
    onShippingQuery = []
    onPreCheckoutQuery = []
    onPoll = []
    onPollAnswer = []
    onChatMemberUpdated = []
    onChatJoinRequest = []
    onRaw = []  # just in case

    async def start(self):
        await self.poller.start()
        await self.worker.start()

    def activate(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.start())
        try:
            loop.run_forever()
        except Exception:  # just any
            loop.stop()

    async def make_request(self, method, data):
        async with self.session.post(self.api_url + self.token + "/" + method, data=data) as post:
            a = await post.json()
            if a["ok"] is False and "parameters" in a and "retry_after" in a["parameters"]:
                await asyncio.sleep(a["parameters"]["retry_after"]+1)
                logging.DEBUG("TOO MANY REQUESTS CATCHED")
                return await self.make_request(method, data)
            logging.debug([data, a])
            return a
        
    async def send_document(
            self,
            chat_id: Union[str, int],
            document: Any,
            message_thread_id: Union[int, None] = None,
            thumb: Any = None,
            caption: Union[str, None] = None,
            parse_mode: Union[str, None] = None,
            caption_entities: Union[list, None] = None,
            disable_content_type_detection: Union[bool, None] = None,
            disable_notification: Union[bool, None] = None,
            protect_content: Union[bool, None] = None,
            reply_to_message_id: Union[int, None] = None,
            allow_sending_without_reply: Union[bool, None] = None,
            reply_markup: Union[str, None] = None
    ):
        data = aiohttp.FormData(quote_fields=False)
        if chat_id:
            data.add_field("chat_id", chat_id and str(chat_id))
        if message_thread_id:
            data.add_field("message_thread_id", message_thread_id)
        if caption:
            data.add_field("caption", chat_id)
        if caption_entities:
            data.add_field("caption_entities", json.dumps(caption_entities))
        if disable_content_type_detection:
            data.add_field("disable_content_type_detection", json.dumps(disable_content_type_detection))
        if disable_notification:
            data.add_field("disable_notification", json.dumps(disable_notification))
        if disable_content_type_detection:
            data.add_field("disable_content_type_detection", json.dumps(disable_content_type_detection))
        if protect_content:
            data.add_field("protect_content", json.dumps(protect_content))
        if reply_to_message_id:
            data.add_field("reply_to_message_id", str(reply_to_message_id))
        if allow_sending_without_reply:
            data.add_field("allow_sending_without_reply", json.dumps(allow_sending_without_reply))
        if reply_markup:
            data.add_field("reply_markup", json.dumps(reply_markup))
        data.add_field("parse_mode", parse_mode or "HTML")
        data.add_field("document", document)
        if thumb:
            data.add_field("thumblike", thumb)
            data.add_field("thumb", "attach://thumblike") # I haven't tested it yet.
        return await self.make_request(
            "sendDocument",
            data
        )
    async def send_message(
            self,
            chat_id: int,
            text: str,
            message_thread_id: Union[int, None] = None,
            parse_mode: Union[str, None] = None,
            entities: Union[List, None] = None,
            disable_web_page_preview: Union[bool, None] = None,
            disable_notification: Union[bool, None] = None,
            protect_content: Union[bool, None] = None,
            reply_to_message_id: Union[int, None] = None,
            allow_sending_without_reply: Union[bool, None] = None,
            reply_markup: Union[dict, None] = None
    ):
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        if message_thread_id is not None:
            payload["message_thread_id"] = message_thread_id
        if parse_mode is None:
            if entities is None:
                payload["parse_mode"] = "HTML"
        else:
            payload["parse_mode"] = parse_mode
        if disable_web_page_preview is not None:
            payload["disable_web_page_preview"] = disable_web_page_preview
        if disable_notification is not None:
            payload["disable_notification"] = disable_notification
        if entities is not None:
            payload["entities"] = json.dumps(entities)
        if protect_content is not None:
            payload["protect_content"] = protect_content
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        if allow_sending_without_reply is not None:
            payload["allow_sending_without_reply"] = allow_sending_without_reply
        if reply_markup is not None:
            payload["reply_markup"] = json.dumps(reply_markup)
        print(payload)
        print(await self.make_request(
            "sendMessage",
            payload
        ))

    # async def send_message(self, chat_id: int, text: str, extra: dict = {}):
    #     payload = {
    #         "chat_id": chat_id,
    #         "text": text
    #     }
    #     logging.debug(text)
    #     payload |= extra
    #     if "parse_mode" not in payload:
    #         payload["parse_mode"] = "HTML"
    #     result = await self.make_request(
    #         "sendMessage",
    #         payload
    #     )
    #     if result["ok"]:
    #         return convert_dict(result["result"], "message")

    async def answer_callback_query(
            self,
            callback_query_id: str,
            text: Union[str, None] = None,
            show_alert: Union[bool, None] = None,
            url: Union[str, None] = None,
            cache_time: Union[int, None] = None
    ):
        payload = {"callback_query_id": callback_query_id}
        if text is not None:
            payload["text"] = text
        if show_alert is not None:
            payload["show_alert"] = show_alert
        if url is not None:
            payload["url"] = url
        if cache_time is not None:
            payload["cache_time"] = cache_time
        await self.make_request(
            "answerCallbackQuery",
            payload
        )

    async def edit_message_text(
            self,
            text: str,
            chat_id: Union[int, str, None] = None,
            message_id: Union[int, None] = None,
            inline_message_id: Union[int, None] = None,
            parse_mode: Union[str, None] = "HTML",
            entities: Union[List, None] = None,
            disable_web_page_preview: Union[bool, None] = None,
            reply_markup: Union[dict, None] = None
    ):
        payload = {
            "text": text
        }
        if chat_id is not None:
            payload["chat_id"] = chat_id
        if message_id is not None:
            payload["message_id"] = message_id
        if inline_message_id is not None:
            payload["inline_message_id"] = inline_message_id
        if parse_mode is not None:
            payload["parse_mode"] = parse_mode
        if entities is not None:
            payload["entities"] = entities
        if disable_web_page_preview is not None:
            payload["disable_web_page_preview"] = disable_web_page_preview
        if reply_markup is not None:
            payload["reply_markup"] = json.dumps(reply_markup)
        await self.make_request(
            "editMessageText",
            payload
        )

