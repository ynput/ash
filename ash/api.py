import time

import requests
from nxtools import critical_error, logging
from pydantic import BaseModel

from .config import config


class User(BaseModel):
    name: str = "anonymous"


class API:
    user: User

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "X-Api-Key": config.api_key,
            }
        )

        while True:
            try:
                response = self.get("users/me")
            except Exception:
                logging.warning("Unable to connect to the server... Retrying")
                time.sleep(5)
                continue
            break

        if not response:
            print(response.text)
            critical_error("Unable to login")
        try:
            self.user = User(**response.json())
        except Exception:
            critical_error("Unable to login")
        logging.info(f"Logged in as {self.user.name}")

    def url_for(self, endpoint: str) -> str:
        return f"{config.server_url.rstrip('/')}/api/{endpoint.strip('/')}"

    def get(self, endpoint: str, params=None, **kwargs) -> requests.Response:
        return self.session.get(self.url_for(endpoint), params=params)

    def post(self, endpoint: str, data=None, json=None, **kwargs) -> requests.Response:
        return self.session.post(self.url_for(endpoint), data=data, json=json, **kwargs)

    def put(self, endpoint: str, data=None, json=None, **kwargs) -> requests.Response:
        return self.session.put(self.url_for(endpoint), data=data, json=json, **kwargs)

    def patch(self, endpoint: str, data=None, json=None, **kwargs) -> requests.Response:
        return self.session.patch(
            self.url_for(endpoint),
            data=data,
            json=json,
            **kwargs,
        )

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        return self.session.delete(self.url_for(endpoint), **kwargs)


api = API()
