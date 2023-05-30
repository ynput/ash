import os
import socket
import sys
from typing import Literal
from urllib.parse import urlparse

from .containers import PODMAN, get_container_client

import dotenv
from nxtools import critical_error, logging, log_traceback
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
    """Infer info from ASH's container.

    We get the "network" and "network_mode" from the current running
    ASH (what runs this code) container.

    These two can be provided via `AYON_NETWORK` and `AYON_NETWORK_MODE`.
    """
    client, api = get_container_client()

    logging.info("Querying existing containers...")
    for container in client.containers.list():
        if PODMAN:
            insp = container.inspect()
        else:
            insp = api.inspect_container(container.id)
        if insp["Config"]["Hostname"] != socket.gethostname():
            logging.debug(
                f"Hostname for container {insp['Name']} doesn't match ash's, ignoring."
            )
            continue
        break
    else:
        logging.error("Weird, no container found for this host")
        sys.exit(1)

    try:
        network = next(iter(insp["NetworkSettings"]["Networks"].keys()), None)
        network_mode = insp["HostConfig"]["NetworkMode"]
    except Exceptions as e:
        logging.error(
            "ASH is not running in a defined network... make sure it's in"
            "the same network as ayon-docker containers.")
        log_traceback(e)

    return {"network": network, "network_mode": network_mode}


def get_config() -> Config:
    data = {}
    for key, val in os.environ.items():
        key = key.lower()
        if not key.startswith("ayon_"):
            continue
        if key == "ayon_server_url":
            # We won't be able to connect if we receive an `AYON_SERVER_URL`
            # such as `http://localhost:5000` or `http://ayon-docker_server_1`
            # So here we try to resolve it to an actual IP. If we fail, means
            # we can't reach the backend at all.
            try:
                original_value = val
                server_hostname = urlparse(val).hostname
                server_ip = socket.gethostbyname(server_hostname)
                val = val.replace(server_hostname, server_ip)
            except Exception as e:
                critical_error(
                    "Unable to resolve `AYON_SERVER_URL` {original_value}"
                )

        data[key.replace("ayon_", "", 1)] = val
    try:
        config = Config(**data)
    except ValidationError as e:
        for error in e.errors():
            error_desc = error["msg"]
            error_loc = ".".join(str(loc) for loc in error["loc"])
            logging.error(f"Invalid configuration at {error_loc}: {error_desc}")

        critical_error("Unable to configure API")

    if config.network is None and config.network_mode is None:
        local_info = get_local_info()
        config.network = local_info["network"]
        config.network_mode = local_info["network_mode"]

    logging.debug(f"ASH Config is: {config}")
    return config


config = get_config()
