"""Nightly job."""
from orders.processor import OrderProcessor


def run(store, queue):
    processor = OrderProcessor(store)
    while not queue.empty():
        processor.process(queue.get())
