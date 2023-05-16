import time

from typing import Any
from nxtools import logging
from datetime import datetime

from .api import api
from .config import config
from .health import get_health
from .services import Services
from .common import OPModel, Field


class ServiceConfigModel(OPModel):
    volumes: list[str] | None = Field(None, title="Volumes", example=["/tmp:/tmp"])
    ports: list[str] | None = Field(None, title="Ports", example=["8080:8080"])
    mem_limit: str | None = Field(None, title="Memory Limit", example="1g")
    user: str | None = Field(None, title="User", example="1000")
    env: dict[str, Any] = Field(default_factory=dict)


class ServiceDataModel(ServiceConfigModel):
    image: str | None = Field(None, example="ayon/ftrack-addon-leecher:2.0.0")


class ServiceModel(OPModel):
    name: str = Field(...)
    hostname: str = Field(..., example="worker03")
    addon_name: str = Field(..., example="ftrack")
    addon_version: str = Field(..., example="2.0.0")
    service: str = Field(..., example="leecher")
    should_run: bool = Field(...)
    is_running: bool = Field(...)
    last_seen: datetime | None = Field(None)
    data: ServiceDataModel = Field(default_factory=ServiceDataModel)


def main():
    health = get_health()

    payload = {
        "hostname": config.hostname,
        "health": health,
        "services": Services.get_running_services(),
    }

    try:
        response = api.post("hosts/heartbeat", json=payload)
        if not response:
            logging.error("no response")
            return
        services = response.json()["services"]
    except Exception:
        logging.error("Unable to connect Ayon server")
        return

    should_run: list[str] = []
    for service_data in services:
        service = ServiceModel(**service_data)

        should_run.append(service.name)
        if not service.data.image:
            continue

        service_config = ServiceConfigModel(**service.data.dict())

        Services.ensure_running(
            service_name=service.name,
            addon_name=service.addon_name,
            addon_version=service.addon_version,
            service=service.service,
            image=service.data.image,
            **service_config,
        )

    Services.stop_orphans(should_run=should_run)


if __name__ == "__main__":
    while "my guitar gently weeps":
        main()
        time.sleep(2)
