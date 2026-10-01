import time
from typing import Any

import requests
from pydantic import BaseModel

from ash.config import config
from ash.logging import logger


class User(BaseModel):
    name: str = "anonymous"


class API:
    user: User

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "X-Api-Key": config.api_key,
            },
        )

        while True:
            try:
                response = self.get("users/me")
            except Exception:
                logger.warning("Unable to connect to the server... Retrying")
                time.sleep(5)
                continue

            if not response:
                logger.error(f"Unable to login. Error: {response.status_code}")
                time.sleep(60)
                continue

            try:
                self.user = User(**response.json())
            except Exception:
                logger.error(f"Unable to login: {response.text}")
                time.sleep(60)
                continue
            break

        logger.info(f"Logged in as {self.user.name}")

    def url_for(self, endpoint: str) -> str:
        return f"{config.server_url.rstrip('/')}/api/{endpoint.strip('/')}"

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        _ = kwargs  # unused for now
        return self.session.get(self.url_for(endpoint), params=params)

    def post(
        self,
        endpoint: str,
        data: Any = None,
        json: Any = None,
        **kwargs: Any,
    ) -> requests.Response:
        return self.session.post(self.url_for(endpoint), data=data, json=json, **kwargs)

    def put(
        self,
        endpoint: str,
        data: Any = None,
        json: Any = None,
        **kwargs: Any,
    ) -> requests.Response:
        return self.session.put(self.url_for(endpoint), data=data, json=json, **kwargs)

    def patch(
        self,
        endpoint: str,
        data: Any = None,
        json: Any = None,
        **kwargs: Any,
    ) -> requests.Response:
        return self.session.patch(
            self.url_for(endpoint),
            data=data,
            json=json,
            **kwargs,
        )

    def delete(self, endpoint: str, **kwargs: Any) -> requests.Response:
        return self.session.delete(self.url_for(endpoint), **kwargs)


api = API()
