from queue import Queue
import threading
import time, re
import logging

from dummy_pipetter import DummyPipetterControl as ProducerControl
from dummy_pipetter import TubeRack
from dummy_robotarm import DummyRobotArm as SpaceshipControl
from dummy_spectrometer import DummySpectrometerRemoteControl as ConsumerControl



class MessageQueue:
    def __init__(self):
        self.q = Queue()
    
    def update_queue_changes(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            print(f"Queue after {func.__name__}: {self.q.queue}")
            return result
        return wrapper
    
    @update_queue_changes
    def get(self):
        return self.q.get()

    @update_queue_changes
    def put(self, args):
        self.q.put(args)
        # print(f"Queue after put: {self.q.queue}")

    @update_queue_changes
    def task_done(self):
        self.q.task_done()
        # print(f"Queue after task_done: {self.q.queue}")

    def no_message(self):
        return (self.q.qsize() == 0)

class Scheduler:
    def __init__(self, producer, spaceship, consumer):
        self.mq = MessageQueue()

        self.producer = producer
        self.spaceship = spaceship
        self.consumer = consumer

    def start(self):
        threads = [
            threading.Thread(target=self.producer.run, args=(self.mq,)),
            threading.Thread(target=self.spaceship.run, args=(self.mq,)),
            threading.Thread(target=self.consumer.run, args=(self.mq,))
        ]
        for thread in threads: thread.start()

        for thread in threads: thread.join()

class DummyProducerDecision:
    def __init__(self, process_order) -> None:
        self.producer = ProducerControl()
        self.process_order = process_order
        print("Producer Initiated")

    def run(self, mq: MessageQueue):
        while True:
            print(" === Producer === ")
            print(process_order)

            if len(process_order) > 0:
                mq.put(f"To Spaceship get Cargo:{process_order[0]}") 
                process_order.pop(0)
                continue

            if mq.no_message(): 
                # print("HIHI")
                mq.put(f"No Product Remain")
                print("Producer Thread ended")
                break

            time.sleep(0.1)

class DummySpaceshipDecision:
    def __init__(self) -> None:
        self.spaceship = SpaceshipControl()
        print("Spaceship Initiated")
    
    def run(self, mq: MessageQueue):
        while True:
            
            print("\n === Spaceship === \n")

            msg = mq.get()

            if msg == "No Product Remain":
                print("Spaceship thread end")
                break

            elif msg.startswith("To Spaceship get Cargo:"):
                id = re.search(r'To Spaceship get Cargo:(\d+)', msg).group(1)
                # print(f"spaceship grabbed cargo {id}")
                mq.task_done()
                # print(f"spaceship has sent cargo {id} to consumer")
                mq.put(f"To Consumer get Cargo:{id}")

            time.sleep(0.1)

class DummyConsumerDecision:
    def __init__(self) -> None:
        self.consumer = ConsumerControl()
        print("Consumer Initiated")
    
    def run(self, mq: MessageQueue):
        while True: 
            
            print(" === Consumer === ")

            msg = mq.get()

            if msg == "No Product Remain": 
                print("Consumer Thread ended")
                break

            elif msg.startswith("To Consumer get Cargo:"):
                id = re.search(r'To Consumer get Cargo:(\d+)', msg).group(1)
                # print(f"Consuming Cargo {id}")
                mq.task_done()
            
            time.sleep(0.1)

if __name__ == "__main__":
    # process_order = [1, 4, 9, 16, 25, 36, 49]
    process_order = [35, 36, 49]
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


    # testing
    producer = DummyProducerDecision(process_order)
    spaceship = DummySpaceshipDecision()
    consumer = DummyConsumerDecision()
    scheduler = Scheduler(producer, spaceship, consumer)
    scheduler.start()