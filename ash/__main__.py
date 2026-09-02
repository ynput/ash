import signal
import sys
import time
from types import FrameType

from ash.api import api
from ash.config import config
from ash.health import get_health
from ash.logging import logger
from ash.models import ServiceConfigModel, ServiceModel
from ash.services import Services

shutdown_requested = False


def handle_shutdown_signal(signum: int, _frame: FrameType | None) -> None:
    global shutdown_requested
    logger.info(f"Received {signal.Signals(signum).name}, shutting down gracefully")
    logger.trace("I can't lie to you about your chances, but you have my sympathies")
    shutdown_requested = True


def main() -> None:
    health = get_health()

    payload = {
        "hostname": config.hostname,
        "health": health,
        "services": Services.get_running_services(),
    }

    try:
        response = api.post("hosts/heartbeat", json=payload)
        if not response:
            logger.error("Heartbeat: No response")
            return
        services = response.json()["services"]
    except Exception:
        logger.error("Unable to connect Ayon server")
        return

    should_run: list[str] = []
    for service_data in services:
        service = ServiceModel(**service_data)

        should_run.append(service.name)
        if not service.data.image:
            continue

        service_config = ServiceConfigModel(**service.data.model_dump())

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
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    signal.signal(signal.SIGINT, handle_shutdown_signal)

    while "my guitar gently weeps":
        main()
        if shutdown_requested:
            break
        time.sleep(2)

    logger.info("Ash stopped")
    sys.exit(0)
