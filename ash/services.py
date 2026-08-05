from typing import Any

import docker
from docker.models.containers import Container

from ash.config import config
from ash.logging import logger
from ash.models import ServiceConfigModel
from ash.service_logging import ServiceLogger
from ash.utils import slugify


class Services:
    client: docker.DockerClient | None = None
    prefix: str = "io.ayon.service"

    @classmethod
    def connect(cls) -> None:
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
    def stop_orphans(cls, should_run: list[str]) -> None:
        if cls.client is None:
            cls.connect()
        if cls.client is None:
            return
        for container in cls.client.containers.list():
            labels = container.labels
            if service_name := labels.get(f"{cls.prefix}.service_name"):
                if service_name in should_run:
                    continue
                logger.warning(f"Stopping service {service_name}")
                container.stop()

    @classmethod
    def spawn(
        cls,
        image: str,
        hostname: str,
        environment: dict[str, str],
        labels: dict[str, str],
        volumes: list[str] | None,
        ports: dict[str, int | None] | None = None,
        **kwargs: Any,
    ) -> Container | None:
        if cls.client is None:
            cls.connect()
        if cls.client is None:
            return None

        container: Container = cls.client.containers.run(
            image=image,
            detach=True,
            auto_remove=True,
            environment=environment,
            hostname=hostname,
            network_mode=config.network_mode,
            network=config.network,
            name=hostname,
            labels=labels,
            volumes=volumes,
            ports=ports,
            **kwargs)
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
    ) -> None:
        if cls.client is None:
            cls.connect()
        if cls.client is None:
            return

        #
        # Check whether it is running already
        #

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
                logger.error("SERVICE MISMATCH. This shouldn't happen. Stopping.")
                container.stop()

            break
        else:
            # And start it
            addon_string = f"{addon_name}:{addon_version}/{service}"
            logger.info(f"Starting {service_name} {addon_string} (image: {image})")

            kwargs = service_config.model_dump()
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

            volumes = service_config.volumes or []
            for bind_mount in config.binds:
                # add global storage from the ash itself
                if not isinstance(bind_mount, str):
                    continue
                target = bind_mount.split(":")[1]
                if target.startswith("/storage"):
                    volumes.append(bind_mount)

            ports: dict[str, int | None] = {}
            if config.network_mode != "host":
                for p in service_config.ports or []:
                    ports_pair = p.split(":")
                    if len(ports_pair) == 1:
                        # Compose-like UX: "8080" means
                        # host 8080 -> container 8080.
                        host_port = int(ports_pair[0])
                        container_port = ports_pair[0]
                        ports[container_port] = host_port
                    elif len(ports_pair) == 2:
                        # Keep UI syntax as host:container and
                        # translate for Docker SDK {container: host}.
                        host_port = int(ports_pair[0])
                        container_port = ports_pair[1]
                        ports[container_port] = host_port

            container = cls.spawn(
                image,
                hostname,
                environment,
                labels,
                volumes or None,
                ports=ports or None,
            )

        # Ensure container logger is running
        ServiceLogger.add(service_name, container)
