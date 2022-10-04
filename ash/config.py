import os
import socket
import dotenv

from pydantic import BaseModel, Field, ValidationError
from nxtools import logging, critical_error

dotenv.load_dotenv()


class Config(BaseModel):
    api_key: str = Field(...)
    server_url: str = Field(...)
    hostname: str = Field(default_factory=socket.gethostname)


def get_config():
    data = {}
    for key, val in os.environ.items():
        key = key.lower()
        if not key.startswith("ay_"):
            continue
        data[key.replace("ay_", "", 1)] = val
    try:
        config = Config(**data)
    except ValidationError as e:
        for error in e.errors():
            logging.error(f"{' '.join(error['loc'])} : {error['msg']} ")
        critical_error("Unable to configure API")
    return config


config = get_config()
