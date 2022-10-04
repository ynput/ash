import docker

from nxtools import logging, slugify
from typing import Any
from .config import config


class Services:
    client: docker.DockerClient | None = None
    prefix: str = "io.openpype.service"

    @classmethod
    def connect(cls):
        cls.client = docker.DockerClient(base_url="unix://var/run/docker.sock")

    @classmethod
    def get_running_ids(cls):
        result: list[int] = []
        if cls.client is None:
            cls.connect()
        for container in cls.client.containers.list():
            labels = container.labels
            if service_id := labels.get(f"{cls.prefix}.service_id"):
                result.append(int(service_id))
        return result

    @classmethod
    def stop_orphans(cls, should_run: list[int]):
        if cls.client is None:
            cls.connect()
        for container in cls.client.containers.list():
            labels = container.labels
            if service_id := labels.get(f"{cls.prefix}.service_id"):
                if int(service_id) in should_run:
                    continue
                logging.warning(f"Stopping service {service_id}")
                container.stop()

    @classmethod
    def ensure_running(
        cls,
        service_id: int,
        addon_name: str,
        addon_version: str,
        service_name: str,
        image: str,
        environment: dict[str, Any] | None = None,
    ):
        if cls.client is None:
            cls.connect()

        if environment is None:
            environment = {}

        if "ay_api_key" not in environment:
            environment["ay_api_key"] = config.api_key

        environment.update(
            {
                "ay_addon_name": addon_name,
                "ay_addon_version": addon_version,
                "ay_server_url": config.server_url,
            }
        )

        hostname = slugify(
            f"aysvc_{addon_name}_{addon_version}_{service_name}", separator="_"
        )

        #
        # Check whether it is running already
        #

        for container in cls.client.containers.list():
            labels = container.labels

            if labels.get(f"{cls.prefix}.service_name") != service_name:
                continue
            if labels.get(f"{cls.prefix}.addon_name") != addon_name:
                continue
            if labels.get(f"{cls.prefix}.addon_version") != addon_version:
                continue

            break
        else:

            # And start it, if not
            logging.info(
                f"Starting {addon_name}:{addon_version}/{service_name} (image: {image})"
            )

            cls.client.containers.run(
                image,
                detach=True,
                auto_remove=True,
                environment=environment,
                hostname=hostname,
                name=hostname,
                labels={
                    f"{cls.prefix}.service_id": str(service_id),
                    f"{cls.prefix}.service_name": service_name,
                    f"{cls.prefix}.addon_name": addon_name,
                    f"{cls.prefix}.addon_version": addon_version,
                },
            )
