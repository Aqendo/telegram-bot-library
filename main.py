import aiohttp
import asyncio
from typing import Union


class Poller:
    def __init__(self, token, queue: asyncio.Queue, session, api_url: Union[str, None] = "api.telegram.org"):
        self.queue = queue
        self.token = token
        self.session = session
        self.api_url = "https://" + api_url + "/bot"

    async def make_request(self, method, data):
        async with self.session.post(self.api_url + self.token + "/" + method, data=data) as post:
            a = await post.json()
            print(a)
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
    def __init__(self, token: str, n: int, api_url: Union[str, None] = "api.telegram.org"):
        self.queue = asyncio.Queue()
        self.token = token
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        self.poller = Poller(token, self.queue, self.session)
        self.worker = Worker(token, self.queue, n, self.session, self._handle_update)
        self.api_url = "https://" + api_url + "/bot"

    def register(self, method):
        def a(func, preserved=self):
            setattr(preserved, method, func)
            return func

        return a

    async def _handle_update(self, update: dict):
        try:
            tasks = []
            if "message" in update:
                print(update)
                tasks.append(self.onMessage(update["message"]))
                tasks.append(self.onMessageOnly(update["message"]))
            elif "edited_message" in update:
                tasks.append(self.onMessage(update["edited_message"]))
                tasks.append(self.onEditedMessage(update["edited_message"]))
            elif "channel_post" in update:
                tasks.append(self.onMessage(update["channel_post"]))
                tasks.append(self.onChannelPost(update["channel_post"]))
            elif "edited_channel_post" in update:
                tasks.append(self.onMessage(update["edited_channel_post"]))
                tasks.append(self.onEditedChannelPost(update["edited_channel_post"]))
            elif "inline_query" in update:
                tasks.append(self.onInlineQuery(update["inline_query"]))
            elif "chosen_inline_result" in update:
                tasks.append(self.onChosenInlineResult(update["chosen_inline_result"]))
            elif "callback_query" in update:
                tasks.append(self.onCallbackQuery(update["callback_query"]))
            else:
                raise NotImplemented
            await asyncio.gather(*tasks)
        except Exception as e:
            print("ERROR: ", e)

    async def onMessage(self, update):
        pass

    async def onEditedMessage(self, update):
        pass

    async def onEditedChannelPost(self, update):
        pass

    async def onChannelPost(self, update):
        pass

    async def onMessageOnly(self, update):
        pass

    async def onInlineQuery(self, update):
        pass

    async def onChosenInlineResult(self, update):
        pass

    async def onCallbackQuery(self, update):
        pass

    async def onShippingQuery(self, update):
        pass

    async def onPreCheckoutQuery(self, update):
        pass

    async def onPoll(self, update):
        pass

    async def onPollAnswer(self, update):
        pass

    async def onChatMemberUpdated(self, update):
        pass

    async def onChatJoinRequest(self, update):
        pass

    async def start(self):
        await self.poller.start()
        await self.worker.start()

    async def make_request(self, method, data):
        async with self.session.post(self.api_url + self.token + "/" + method, data=data) as post:
            a = await post.json()
            print(a)
            return a