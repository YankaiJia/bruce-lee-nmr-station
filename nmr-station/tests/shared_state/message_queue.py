from queue import Queue
import threading

class MessageQueue:
    def __init__(self):
        self.q = Queue()
        self.lock = threading.Lock()
    
    def update_queue_changes(func):
        def wrapper(self, *args, **kwargs):
            print(f"Queue before {func.__name__}: {self.q.queue}")
            result = func(self, *args, **kwargs)
            print(f"Queue after {func.__name__}: {self.q.queue}")
            return result
        return wrapper
    
    @update_queue_changes
    def get_front_message(self) -> str:
        with self.lock:
            return list(self.q.queue)[0]

    @update_queue_changes
    def add_new_message(self, args):
        with self.lock:
            self.q.put(args)

    @update_queue_changes
    def finish_front_message(self):
        with self.lock:
            self.q.get()
            self.q.task_done()

    def no_message(self):
        return (self.q.qsize() == 0)