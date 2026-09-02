import docker
from docker.models.containers import Container

from ash.config import config
from ash.logging import logger
from ash.models import RegistryAuth, ServiceConfigModel
from ash.service_logging import ServiceLogger
from ash.utils import slugify


class UnableToStartError(Exception):
    pass


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
        *,
        environment: dict[str, str] | None = None,
        labels: dict[str, str] | None = None,
        volumes: list[str] | None = None,
        registry_auth: RegistryAuth | None = None,
    ) -> Container | None:
        if cls.client is None:
            cls.connect()

        if cls.client is None:
            return None

        # pull the image explicitly to avoid issues with private registries
        # and to update the image if it has changed

        try:
            cls.client.images.pull(
                image,
                auth_config=registry_auth.model_dump() if registry_auth else None,
            )

            container: Container = cls.client.containers.run(
                image,
                name=hostname,
                detach=True,
                auto_remove=True,
                hostname=hostname,
                network_mode=config.network_mode,
                network=config.network,
                environment=environment or {},
                labels=labels or {},
                volumes=volumes or [],
            )
        except Exception as e:
            raise UnableToStartError(f"Unable to pull image {image}: {e}") from e

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
        registry_auth: RegistryAuth | None = None,
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

            try:
                container = cls.spawn(
                    image,
                    hostname=hostname,
                    environment=environment,
                    labels=labels,
                    volumes=volumes or None,
                    registry_auth=registry_auth,
                )
            except UnableToStartError as e:
                logger.error(f"Unable to start service {service_name}: {e}")
                return

        # Ensure container logger is running
        if isinstance(container, Container):
            ServiceLogger.add(service_name, container)
