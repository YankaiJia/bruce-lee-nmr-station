import threading

from .tube_manager import TubeManager
from .message_queue import MessageQueue

class SharedState:
    def __init__(self) -> None:
        # number of tubes use
        # self.tube = TubeManager(4)
        self.tube = TubeManager(2)
        self.producer_message_queue = MessageQueue()
        self.consumer_message_queue = MessageQueue()
        self.lock = threading.Lock()