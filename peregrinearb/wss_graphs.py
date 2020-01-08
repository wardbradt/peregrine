import cryptosockets
import asyncio
import order_book_trackers


class WSSHandler:

    def __init__(self, exchange, tracker):
        self.exchange = exchange
        self.tracker = tracker

