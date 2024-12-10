from datetime import datetime, timedelta
from typing import NoReturn

from instamubble.client.aiohttp import AiohttpClient


class API:
    API_AUTH_URL = "https://api.sendpulse.com/oauth/access_token"

    def __init__(self, client_id: str, client_secret: str, *, http = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.http = http or AiohttpClient()

        self.payload: dict = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        self.__token: str | None = None
        self.__expiration_time: datetime | None = None

    async def _generate_token(self) -> NoReturn:
        """
        New token generation
        """
        response = await self.http.request_json(
            self.API_AUTH_URL, "POST", json=self.payload
        )
        self.__token = response["access_token"]
        expires_in = response["expires_in"]
        self.__expiration_time = datetime.now() + timedelta(seconds=expires_in)

    async def get_access_token(self) -> str:
        """
        Getting current token.
        """
        if self.__token is None or datetime.now() >= self.__expiration_time:
            await self._generate_token()

        return self.__token
