import os
import socket
import sys
from typing import Any, Literal

import docker
import dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator

dotenv.load_dotenv()


LogLevel = Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class BaseConfig(BaseModel):
    api_key: str = Field(...)
    server_url: str = Field("http://ayon:5000")
    hostname: str = Field(default_factory=socket.gethostname)
    network: str | None = Field(default=None)
    network_mode: str | None = Field(default=None)

    log_mode: Literal["text", "json"] = Field(
        default="text",
        description="Log output format",
    )

    log_level: LogLevel = Field(
        default="DEBUG",
        description="Log level for the console output",
    )

    log_context: bool = Field(
        default=False,
        description="Print log context along with the message",
    )

    @field_validator("log_level", mode="before")
    def validate_log_level(cls, value: str) -> str:  # noqa: N805
        return value.upper()


class Config(BaseConfig):
    binds: list[str] = Field(default_factory=list)


def get_local_info() -> dict[str, Any]:
    client = docker.DockerClient(base_url="unix://var/run/docker.sock")
    api = docker.APIClient(base_url="unix://var/run/docker.sock")
    for container in client.containers.list():
        insp = api.inspect_container(container.id)
        if insp["Config"]["Hostname"] != socket.gethostname():
            continue
        break
    else:
        print("Weird, no container found for this host")  # noqa: T201
        sys.exit(1)

    networks = insp["NetworkSettings"]["Networks"]

    return {
        "networks": list(networks.keys()),
        "binds": insp["HostConfig"]["Binds"],
    }


def get_config() -> Config:
    data = {}
    for key, val in os.environ.items():
        lkey = key.lower()
        if not lkey.startswith("ayon_"):
            continue
        data[lkey.replace("ayon_", "", 1)] = val
    try:
        base_config = BaseConfig(**data)
    except ValidationError as e:
        for error in e.errors():
            error_desc = error["msg"]
            error_loc = ".".join(str(loc) for loc in error["loc"])

            print(  # noqa: T201
                f"Error in config: {error_desc} at {error_loc}",
                file=sys.stderr,
                flush=True,
            )

        sys.exit(1)

    local_info = get_local_info()

    config = Config(**base_config.model_dump(), binds=local_info["binds"])

    if config.network is None and config.network_mode is None:
        config.network = local_info["networks"][0]

    # logging.debug(
    #     f"Configured worker {config.hostname} to connect to {config.server_url}"
    # )
    return config


config = get_config()
