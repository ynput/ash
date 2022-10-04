import time

from nxtools import logging

from .api import api
from .config import config
from .health import get_health
from .services import Services


def main():
    health = get_health()

    payload = {
        "hostname": config.hostname,
        "health": health,
        "services": Services.get_running_ids(),
    }

    response = api.post("hosts/heartbeat", json=payload)
    if not response:
        logging.error("no response")
        return

    services = response.json()["services"]
    should_run: list[int] = []
    for service in services:
        should_run.append(service["id"])
        Services.ensure_running(
            service_id=service["id"],
            addon_name=service["addonName"],
            addon_version=service["addonVersion"],
            service_name=service["serviceName"],
            image=service["image"],
        )

    Services.stop_orphans(should_run=should_run)


if __name__ == "__main__":
    while "my guitar gently weeps":
        main()
        time.sleep(2)
