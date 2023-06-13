import os
import socket
import sys
from typing import Literal

import docker
import dotenv
from nxtools import critical_error, logging
from pydantic import BaseModel, Field, ValidationError

logging.user = "ash"
dotenv.load_dotenv()


class Config(BaseModel):
    api_key: str = Field(...)
    server_url: str = Field("http://ayon:5000")
    hostname: str = Field(default_factory=socket.gethostname)
    network: str | None = Field(default=None)
    network_mode: str | None = Field(default=None)
    log_driver: Literal["loki"] | None = Field(default=None)
    loki_url: str | None = Field(default=None)


def get_local_info():
    client = docker.DockerClient(base_url="unix://var/run/docker.sock")
    api = docker.APIClient(base_url="unix://var/run/docker.sock")
    for container in client.containers.list():
        insp = api.inspect_container(container.id)
        if insp["Config"]["Hostname"] != socket.gethostname():
            continue
        # print(json.dumps(insp, indent=4))
        break
    else:
        logging.error("Weird, no container found for this host")
        sys.exit(1)

    networks = insp["NetworkSettings"]["Networks"]

    return {"networks": list(networks.keys())}


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
            error_desc = error["msg"]
            error_loc = ".".join(str(loc) for loc in error["loc"])
            logging.error(f"Invalid configuration at {error_loc}: {error_desc}")

        critical_error("Unable to configure API")

    local_info = get_local_info()

    if config.network is None and config.network_mode is None:
        config.network = local_info["networks"][0]

    return config


config = get_config()
