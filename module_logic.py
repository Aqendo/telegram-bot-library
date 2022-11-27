from .bot import Bot

class BaseModule:
    def __init__(self, bot: Bot):
        self.bot = bot

    def get_funcs(self):
        return []
