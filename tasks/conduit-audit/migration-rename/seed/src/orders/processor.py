"""Order processing module."""


class OrderProcessor:
    """Processes orders end to end."""

    def __init__(self, store):
        self.store = store

    def process(self, order):
        self.store.save(order)
        return order["id"]
