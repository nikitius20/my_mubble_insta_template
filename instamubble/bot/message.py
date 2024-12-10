from aiohttp import ContentTypeError

from instamubble.api.api import API
from instamubble.types.message import MessageType


class Message:
    URL = "https://api.sendpulse.com/instagram/contacts/send"

    def __init__(
        self,
        user_id: str,
        name: str | None,
        username: str | None,
        text: str | None,
        data: str | None = None,
        message_type: MessageType = MessageType.TEXT,
        *,
        api: API,
    ):
        self.user_id = user_id
        self.name = name
        self.username = username
        self.text = text
        self.data = data
        self.message_type = message_type
        self._api = api

    async def answer(self, text: str | None = None) -> dict:
        """
        Sends a message back to the contact. Логика в зависимости от message_type:
        - Если TEXT, отправляем текстовое сообщение.
        - Если IMAGE, отправляем изображение по URL из self.data.
        - Если AUDIO, отправляем аудио по URL из self.data.
        """
        token = await self._api.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        if text is None:
            text = self.text or ""
        chunks = [text[i : i + 1000] for i in range(0, len(text), 1000)]
        for chunk in chunks:
            payload = {
                "contact_id": self.user_id,
                "messages": [{"type": "text", "message": {"text": chunk}}],
            }
            response = await self._api.http.request_raw(
                self.URL, "POST", headers=headers, json=payload
            )
            if response.status != 200:
                return await self._error_response(response)
        return {"status": "success", "details": "Text message sent successfully"}

    async def _error_response(self, response):
        response_text = await response.text()
        try:
            response_data = await response.json(encoding="utf-8")
            return {"error": response_data, "details": response_text}
        except ContentTypeError:
            return {
                "error": "Response is not JSON format",
                "details": response_text,
            }
