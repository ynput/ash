from typing import Any

import docker
from nxtools import logging, slugify

from .config import config
from .models import ServiceConfigModel


class Services:
    client: docker.DockerClient | None = None
    prefix: str = "io.ayon.service"

    @classmethod
    def connect(cls):
        cls.client = docker.DockerClient(base_url="unix://var/run/docker.sock")

    @classmethod
    def get_running_services(cls) -> list[str]:
        result: list[str] = []
        if cls.client is None:
            cls.connect()

        if cls.client is None:
            return result

        for container in cls.client.containers.list():
            labels = container.labels
            if service_name := labels.get(f"{cls.prefix}.service_name"):
                result.append(service_name)
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
    def ensure_running(
        cls,
        service_name: str,
        addon_name: str,
        addon_version: str,
        service: str,
        image: str,
        service_config: ServiceConfigModel,
        environment: dict[str, Any] | None = None,
    ):
        if cls.client is None:
            cls.connect()

        if environment is None:
            environment = {}

        if "ayon_api_key" not in environment:
            environment["ayon_api_key"] = config.api_key

        environment.update(
            {
                "ayon_addon_name": addon_name,
                "ayon_addon_version": addon_version,
                "ayon_server_url": config.server_url,
                "ayon_service_name": service_name,
            }
        )

        hostname = slugify(
            f"aysvc_{service_name}",
            separator="_",
        )

        #
        # Check whether it is running already
        #

        if cls.client is None:
            return

        for container in cls.client.containers.list():
            labels = container.labels

            if labels.get(f"{cls.prefix}.service_name") != service_name:
                continue

            if (
                labels.get(f"{cls.prefix}.service") != service
                or labels.get(f"{cls.prefix}.addon_name") != addon_name
                or labels.get(f"{cls.prefix}.addon_version") != addon_version
            ):
                logging.error("SERVICE MISMATCH. This shouldn't happen. Stopping.")
                container.stop()

            break
        else:
            # And start it
            addon_string = f"{addon_name}:{addon_version}/{service}"
            logging.info(f"Starting {service_name} {addon_string} (image: {image})")

            env = {k.upper(): v for k, v in environment.items()}
            env.update(service_config.env)

            kwargs = service_config.dict()
            kwargs.pop("env", None)

            cls.client.containers.run(
                image,
                detach=True,
                auto_remove=True,
                environment=env,
                hostname=hostname,
                network_mode=config.network_mode,
                network=config.network,
                name=hostname,
                labels={
                    f"{cls.prefix}.service_name": service_name,
                    f"{cls.prefix}.service": service,
                    f"{cls.prefix}.addon_name": addon_name,
                    f"{cls.prefix}.addon_version": addon_version,
                },
                **kwargs,
            )
