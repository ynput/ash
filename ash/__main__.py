import time

from typing import Any
from nxtools import logging
from datetime import datetime

from .api import api
from .config import config
from .health import get_health
from .services import Services
from .common import OPModel, Field


class ServiceDataModel(OPModel):
    image: str | None = Field(None, example="ynput/ayon-ftrack-leecher:2.0.0")
    env: dict[str, Any] = Field(default_factory=dict)


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
    except Exception as e:
        logging.error("error: %s", e)

    should_run: list[str] = []
    for service_data in services:
        service = ServiceModel(**service_data)

        should_run.append(service.name)
        if not service.data.image:
            continue

        Services.ensure_running(
            service_name=service.name,
            addon_name=service.addon_name,
            addon_version=service.addon_version,
            service=service.service,
            image=service.data.image,
        )

    Services.stop_orphans(should_run=should_run)


if __name__ == "__main__":
    while "my guitar gently weeps":
        main()
        time.sleep(2)
