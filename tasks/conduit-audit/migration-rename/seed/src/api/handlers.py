"""HTTP handlers."""
from orders import OrderProcessor


def post_order(request, store):
    processor = OrderProcessor(store)
    return processor.process(request.json)
