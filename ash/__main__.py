import time

from nxtools import logging

from .api import api
from .config import config
from .health import get_health
from .models import ServiceConfigModel, ServiceModel
from .services import Services


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
            service_config=service_config,
        )

    Services.stop_orphans(should_run=should_run)


if __name__ == "__main__":
    while "my guitar gently weeps":
        main()
        time.sleep(2)
