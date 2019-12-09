from queue import Queue

from threading import Thread
import sys

# NOTE: We can use separate files for sender&receiver logging, or for threads ?
# For now, everything is sequential for easier debugging (which was sent after which was received)


class SafeWriter:
    # A thread safe, realtime file writer (Used for logging across all threads)
    def __init__(self, *args):
        self.file_writer = open(*args)
        self.queue = Queue()
        self.finished = False
        Thread(name='SafeWriter', target=self.internal_writer).start()

    def write(self, data):
        self.queue.put(data + '\n')

    def internal_writer(self):
        while not self.finished:
            try:
                data = self.queue.get(True, 1)
            except Exception:
                # Supposedly an Empty exception
                continue
            self.file_writer.write(data)
            self.file_writer.flush()  # To write instantaneously
            self.queue.task_done()

    def close(self):
        self.queue.join()
        self.finished = True
        self.file_writer.close()
