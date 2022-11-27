import aiohttp
import asyncio
import logging
import traceback
import json
from typing import Union, List
from .types import Handlers, convert_dict, BaseModule
from functools import wraps, partial


class Poller:
    def __init__(self, token, queue: asyncio.Queue, session, api_url: Union[str, None] = "api.telegram.org"):
        self.queue = queue
        self.token = token
        self.session = session
        self.api_url = "https://" + api_url + "/bot"

    async def make_request(self, method, data):
        async with self.session.post(self.api_url + self.token + "/" + method, data=data) as post:
            a = await post.json()
            logging.debug(a)
            return a

    async def _worker(self):
        offset = -1
        while True:
            res = await self.make_request("getUpdates", {"offset": offset})
            for i in res['result']:
                offset = i['update_id'] + 1
                self.queue.put_nowait(i)

    async def start(self):
        asyncio.create_task(self._worker())


class Worker:
    def __init__(self, token: str, queue: asyncio.Queue, concurrent_workers: int, session, handle_update):
        self.token = token
        self.queue = queue
        self.concurrent_workers = concurrent_workers
        self.session = session
        self.handle_update = handle_update

        # print(update)

    async def _worker(self):
        while True:
            upd = await self.queue.get()
            await self.handle_update(upd)

    async def start(self):
        for _ in range(self.concurrent_workers):
            asyncio.create_task(self._worker())


class Bot:
    def __init__(self, token: str, n: int, api_url: Union[str, None] = "api.telegram.org", skip_updates: bool = True):
        self.queue = asyncio.Queue()
        if not isinstance(token, str) or len(token) == 0:
            raise ValueError("A valid token must be provided.")
        self.token = token
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(
        #    headers={
        #    'Content-Type': 'application/json'
        #}
        )
        self.poller = Poller(token, self.queue, self.session)
        self.worker = Worker(token, self.queue, n, self.session, self._handle_update)
        self.api_url = "https://" + api_url + "/bot"
    
    # We should close the connection of aiohttp to prevent memory leaks
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

    def wrap(self, func):
        @wraps(func)
        async def run(*args, loop=None, executor=None, **kwargs):
            if loop is None:
                loop = asyncio.get_event_loop()
            pfunc = partial(func, *args, **kwargs)
            return await loop.run_in_executor(executor, pfunc)
        return run
    
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
            else:
                logging.error("Unknown update type: %s" % lsit(update.keys())[1])
            tasks += [func(update) for func in self.onRaw]
            
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
                print("TOO MANY REQUESTS CATCHED")
                return await self.make_request(method, data)
            # print(data, a)
            return a

    async def send_document(
            self,
            document,
            chat_id
    ):
        data = aiohttp.FormData(quote_fields=False)
        data.add_field("chat_id", str(chat_id))
        data.add_field("document", document)
        await self.make_request(
            "sendDocument",
            data
        )

    async def send_message(
            self,
            chat_id: int,
            text: str,
            message_thread_id: Union[int, None] = None,
            parse_mode: Union[str, None] = "HTML",
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
        if parse_mode is not None:
            payload["parse_mode"] = parse_mode
        if disable_web_page_preview is not None:
            payload["disable_web_page_preview"] = disable_web_page_preview
        if disable_notification is not None:
            payload["disable_notification"] = disable_notification
        if entities is not None:
            payload["entities"] = entities
        if protect_content is not None:
            payload["protect_content"] = protect_content
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        if allow_sending_without_reply is not None:
            payload["allow_sending_without_reply"] = allow_sending_without_reply
        if reply_markup is not None:
            payload["reply_markup"] = json.dumps(reply_markup)
        # print(payload)
        result = await self.make_request(
            "sendMessage",
            payload
        )
        if result["ok"] is True:
            return convert_dict(result["result"], "message")
        else:
            return None

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

