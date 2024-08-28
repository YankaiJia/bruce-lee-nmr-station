import threading, sys, os

sys.path.append(os.path.abspath(os.path.pardir))

from .tube_manager import TubeManager
from .message_queue import MessageQueue
from settings import TUBE_COUNT

class SharedState:
    def __init__(self) -> None:
        # number of tubes use
        self.tube = TubeManager(TUBE_COUNT)
        self.producer_message_queue = MessageQueue()
        self.consumer_message_queue = MessageQueue()
        self.lock = threading.Lock()