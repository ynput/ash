from nxtools import logging, slugify

from .config import config
from .containers import get_container_client
from .models import ServiceConfigModel
from .service_logging import ServiceLogger


class Services:
    client = None
    prefix: str = "io.ayon.service"

    @classmethod
    def connect(cls):
        client, _ = get_container_client()
        cls.client = client

    @classmethod
    def get_running_services(cls) -> list[str]:
        result: list[str] = []
        if cls.client is None:
            cls.connect()
        if cls.client is None:
            return result

        logging.debug("Checking for Running services.")

        for container in cls.client.containers.list():
            labels = container.labels
            if service_name := labels.get(f"{cls.prefix}.service_name"):
                result.append(service_name)
        logging.debug("Found {0} running services: {1}".format(len(result), result))
        return result

    @classmethod
    def stop_orphans(cls, should_run: list[str]):
        if cls.client is None:
            cls.connect()
        if cls.client is None:
            return
        for container in cls.client.containers.list():
            labels = container.labels
            if service_name := labels.get(f"{cls.prefix}.service_name"):
                if service_name in should_run:
                    continue
                logging.warning(f"Stopping service {service_name}")
                container.stop()

    @classmethod
    def spawn(
        cls,
        image: str,
        hostname: str,
        environment: dict[str, str],
        labels: dict[str, str],
        **kwargs,
    ):
        if cls.client is None:
            cls.connect()
        if cls.client is None:
            return

        container = cls.client.containers.run(
            image,
            detach=True,
            auto_remove=True,
            environment=environment,
            hostname=hostname,
            network_mode=config.network_mode,
            network=config.network,
            name=hostname,
            labels=labels,
            **kwargs,
        )
        return container

    @classmethod
    def ensure_running(
        cls,
        service_name: str,
        addon_name: str,
        addon_version: str,
        service: str,
        image: str,
        service_config: ServiceConfigModel,
    ):
        if cls.client is None:
            cls.connect()
        if cls.client is None:
            return

        #
        # Check whether it is running already
        #
        logging.info("Checking if Service is already running.")
        container = None

        for container in cls.client.containers.list():
            labels = container.labels

            if labels.get(f"{cls.prefix}.service_name") != service_name:
                continue

            try:
                assert labels.get(f"{cls.prefix}.service") == service
                assert labels.get(f"{cls.prefix}.addon_name") == addon_name
                assert labels.get(f"{cls.prefix}.addon_version") == addon_version
            except AssertionError:
                logging.error("SERVICE MISMATCH. This shouldn't happen. Stopping.")
                container.stop()
            else:
                logging.debug(
                    f"Service {service_name} already running at {container.id}"
                )
            break
        else:
            # And start it
            addon_string = f"{addon_name}:{addon_version}/{service}"
            logging.info(f"Starting {service_name} {addon_string} (image: {image})")

            kwargs = service_config.dict()
            hostname = slugify(f"aysvc_{service_name}", separator="_")

            environment = {
                "AYON_SERVER_URL": config.server_url,
                "AYON_API_KEY": config.api_key,
                "AYON_ADDON_NAME": addon_name,
                "AYON_ADDON_VERSION": addon_version,
                "AYON_SERVICE_NAME": service_name,
                **kwargs.pop("env", {}),
            }

            labels = {
                f"{cls.prefix}.service_name": service_name,
                f"{cls.prefix}.service": service,
                f"{cls.prefix}.addon_name": addon_name,
                f"{cls.prefix}.addon_version": addon_version,
            }

            container = cls.spawn(image, hostname, environment, labels)

        ServiceLogger.add(service_name, container)
