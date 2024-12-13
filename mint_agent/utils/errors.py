class AgentError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ServerError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class LLMServiceUnavailableError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)
