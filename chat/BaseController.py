from typing import Text, Dict, List
from abc import ABC, abstractmethod
from TimeLogger import TimeLogger

class BaseController(ABC):
    """ Class to control conversation """

    default_base_url = None
    default_model = None
    default_api_key = None
    default_temperature = 0.1
    client = None
    temperature = None
    model = None
    base_url = None
    api_key = None
    timelogger = TimeLogger()

    def __init__(self, model_name, url, api_key, temperature):
        self.base_url = url or self.default_base_url # Server URL
        self.model = model_name or self.default_model # Model name
        self.temperature = temperature or self.default_temperature # Temperature
        self.api_key = api_key or self.default_api_key  # API KEY

    @abstractmethod
    def getClient(self) :
        """
        This class is an abstract class that is used to define the interface for the OpenAI API controllers.
        The class has methods"""