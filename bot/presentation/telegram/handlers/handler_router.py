from telethon import events

from .out_handler import OutHandler
from .in_handler import InHandler


class HandlerRouter:
    """Маршрутизатор между in и out обработчиками"""

    def __init__(self, out_handler: OutHandler, in_handler: InHandler):
        self.out_handler = out_handler
        self.in_handler = in_handler

    async def handle(self, event: events.NewMessage.Event):
        if event.message.out:
            await self.out_handler.handle(event)
        else:
            await self.in_handler.handle(event)