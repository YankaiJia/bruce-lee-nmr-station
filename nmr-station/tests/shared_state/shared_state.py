import threading

from .tube_manager import TubeManager
from .message_queue import MessageQueue

class SharedState:
    def __init__(self) -> None:
        self.tube = TubeManager(4)
        self.message_queue = MessageQueue()
        self.lock = threading.Lock()

    def no_message(self) -> bool:
        with self.lock:
            return (self.message_queue.qsize() == 0)

    def get_front_message(self) -> str :
        with self.lock:
            return list(self.message_queue.queue)[0]
    
    def add_new_message(self, message: str):
        with self.lock:
            self.message_queue.put(message)
    
    def finish_front_message(self):
        self.message_queue.get()
        self.message_queue.task_done()