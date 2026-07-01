import httpx
from typing import Optional, Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from app.config import get_settings


class BaseAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.settings = get_settings()
        self.client = httpx.AsyncClient(
            timeout=self.settings.HTTP_TIMEOUT,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if endpoint else self.base_url

        response = await self.client.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, json_data: Dict) -> Dict:
        return await self._request("POST", endpoint, json_data=json_data)

    async def close(self):
        await self.client.aclose()
