import threading

from .tube_manager import TubeManager
from .message_queue import MessageQueue

class SharedState:
    def __init__(self) -> None:
        self.tube = TubeManager(4)
        self.message_queue = MessageQueue()
        self.lock = threading.Lock()