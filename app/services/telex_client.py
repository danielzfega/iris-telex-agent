import httpx
from . import config
from loguru import logger

class TelexClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=15.0)

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def send_dm(self, recipient_id: str, content: str):
        """
        Sends a DM to user via Telex API.
        Adapt endpoint path to your Telex workspace.
        """
        url = f"{self.base_url}/v1/messages"
        payload = {
            "type": "direct_message",
            "recipient_id": recipient_id,
            "content": content
        }
        logger.info("Sending DM to %s", recipient_id)
        r = await self._client.post(url, json=payload, headers=self._headers())
        r.raise_for_status()
        return r.json()

    async def post_message_to_channel(self, channel_id: str, content: str):
        url = f"{self.base_url}/v1/channels/{channel_id}/messages"
        r = await self._client.post(url, json={"content": content}, headers=self._headers())
        r.raise_for_status()
        return r.json()
