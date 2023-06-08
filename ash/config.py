import os
import json
import socket
import sys

import docker
import dotenv

from typing import Literal

from pydantic import BaseModel, Field, ValidationError
from nxtools import logging, critical_error

logging.user = "ash"
dotenv.load_dotenv()


class Config(BaseModel):
    api_key: str = Field(...)
    server_url: str = Field(...)
    hostname: str = Field(default_factory=socket.gethostname)
    network_mode: str = Field(default="bridge")
    log_driver: Literal["loki"] | None = Field(default=None)
    loki_url: str | None = Field(default=None)


def get_config() -> Config:
    data = {}
    for key, val in os.environ.items():
        key = key.lower()
        if not key.startswith("ayon_"):
            continue
        data[key.replace("ayon_", "", 1)] = val
    try:
        config = Config(**data)
    except ValidationError as e:
        for error in e.errors():
            logging.error(f"{' '.join(error['loc'])} : {error['msg']} ")
        critical_error("Unable to configure API")
    return config


def get_local_info():
    client = docker.DockerClient(base_url="unix://var/run/docker.sock")
    api = docker.APIClient(base_url="unix://var/run/docker.sock")
    for container in client.containers.list():
        insp = api.inspect_container(container.id)
        if insp["Config"]["Hostname"] != socket.gethostname():
            continue

        print(json.dumps(insp, indent=4))
        break
    else:
        logging.error("Weird, no container found for this host")
        sys.exit(1)


get_local_info()
sys.exit(0)

config = get_config()
