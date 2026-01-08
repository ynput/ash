__all__ = ["OPModel", "Field"]


from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


def camelize(src: str) -> str:
    """Convert snake_case to camelCase."""
    components = src.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class OPModel(BaseModel):
    """Base API model."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        alias_generator=camelize,
    )


class ServiceConfigModel(OPModel):
    volumes: Annotated[
        list[str] | None,
        Field(
            title="Volumes",
            examples=[["/tmp:/tmp"]],
        ),
    ] = None

    ports: Annotated[
        list[str] | None,
        Field(
            title="Ports",
            examples=[["8080:8080"]],
        ),
    ] = None

    mem_limit: Annotated[
        str | None,
        Field(
            title="Memory Limit",
            examples=["1g"],
        ),
    ] = None

    user: Annotated[
        str | None,
        Field(
            title="User",
            examples=["1000"],
        ),
    ] = None

    env: Annotated[
        dict[str, Any],
        Field(
            default_factory=dict,
        ),
    ]


class DockerLogin(OPModel):
    registry: Annotated[
        str,
        Field(
            title="Registry URL",
            examples=["https://my-registry.com/v1/"],
        ),
    ]

    username: Annotated[
        str,
        Field(
            title="Registry Username",
            examples=["my-username"],
        ),
    ]

    password: Annotated[
        str,
        Field(
            title="Registry Password",
            examples=["my-password"],
        ),
    ]

    email: Annotated[
        str | None,
        Field(
            title="Registry Email",
            examples=["me@home.com"],
        ),
    ] = None


class ServiceDataModel(ServiceConfigModel):
    image: Annotated[
        str | None,
        Field(
            examples=["ayon/ftrack-addon-leecher:2.0.0"],
        ),
    ] = None

    login: Annotated[
        DockerLogin | None,
        Field(
            title="Docker Login",
        ),
    ] = None


class ServiceModel(OPModel):
    name: Annotated[
        str,
        Field(
            title="Service Name",
            description="Unique service name",
            examples=["ftrack-leecher"],
        ),
    ]

    hostname: Annotated[
        str,
        Field(
            title="Host name",
            examples=["worker03"],
        ),
    ]

    addon_name: Annotated[
        str,
        Field(
            title="Addon name",
            examples=["ftrack"],
        ),
    ]

    addon_version: Annotated[
        str,
        Field(
            title="Addon version",
            examples=["2.0.0"],
        ),
    ]

    service: Annotated[
        str,
        Field(
            title="Service",
            description="Type of service as defined in the addon manifest",
            examples=["leecher"],
        ),
    ]

    should_run: Annotated[
        bool,
        Field(
            title="Should run",
            description="Whether the service is expected to be running or not",
        ),
    ] = False

    is_running: Annotated[
        bool,
        Field(
            title="Is running",
            description="Whether the service is currently running or not",
        ),
    ] = False

    last_seen: Annotated[
        datetime | None,
        Field(
            title="Last seen at",
        ),
    ] = None

    data: Annotated[
        ServiceDataModel,
        Field(default_factory=lambda: ServiceDataModel()),
    ]
