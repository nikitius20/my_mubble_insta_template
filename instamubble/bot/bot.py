import re
from functools import wraps

from aiohttp import web

from instamubble.bot.message import Message
from instamubble.types.message import MessageType


class InstaMubble:
    def __init__(self, api):
        self.api = api

        self._message_handlers = []

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}: {self.api} {self.dispatch} {self.loop_wrapper}"
        )

    def message(self, _: str | MessageType | None = None):
        def decorator(func):

            compiled_pattern = _ if isinstance(_, MessageType) else re.compile(_)
            self._message_handlers.append((compiled_pattern, func))

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    async def handle_message(
        self,
        user_id: str,
        name: str | None,
        username: str | None,
        text: str | None,
        *,
        message_type: MessageType,
        data: str | None = None,
    ):
        message = Message(
            user_id,
            name,
            username,
            text,
            data,
            message_type,
            api=self.api,
        )
        for pattern, handler in self._message_handlers:
            if isinstance(pattern, MessageType):
                if pattern is message_type:
                    await handler(message)
                    break
            else:
                if text is not None and pattern.match(text):
                    await handler(message)
                    break

    async def webhook_handler(self, request):
        webhook_data = await request.json()
        try:
            user_id: str = webhook_data[0]["contact"]["id"]
            name: str | None = webhook_data[0]["contact"].get("name")
            username: str | None = webhook_data[0]["contact"].get("username")

            channel_data = webhook_data[0]["info"]["message"]["channel_data"]["message"]
            text: str | None = channel_data.get("text", None)

            attachments = channel_data.get("attachments", [])
            data = None
            message_type = MessageType.TEXT

            if attachments:
                att_type = attachments[0]["type"].upper()
                data = attachments[0]["payload"]["url"]
                if att_type == "IMAGE":
                    message_type = MessageType.IMAGE
                elif att_type == "AUDIO":
                    message_type = MessageType.AUDIO
                else:
                    message_type = MessageType.TEXT
            else:
                message_type = MessageType.TEXT
        except KeyError:
            return web.Response(status=400, text="Invalid data")

        await self.handle_message(
            user_id, name, username, text, message_type=message_type, data=data
        )

        return web.Response(status=200, text="Processed")

    def run_forever(self, host: str = "0.0.0.0", port: int = 4545):
        app = web.Application()
        app.add_routes([web.post("/webhook", self.webhook_handler)])
        web.run_app(app, host=host, port=port)
