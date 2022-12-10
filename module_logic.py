from abc import ABC, abstractmethod


class BaseModule(ABC):
    @abstractmethod
    def get_funcs(self):
        """
        You need to specify functions
        and their handler types for
        bot to understand them.

        Example:

        return [
            [
                self.some_function_message,
                types.Handlers.onMessage
            ]
        ]
        """
