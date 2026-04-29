"""Smoke test for OrderProcessor."""
from orders import OrderProcessor


class FakeStore:
    def __init__(self):
        self.saved = []

    def save(self, order):
        self.saved.append(order)


def test_processor_saves():
    store = FakeStore()
    p = OrderProcessor(store)
    assert p.process({"id": 1}) == 1
    assert store.saved == [{"id": 1}]
