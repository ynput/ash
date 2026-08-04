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


class ServiceDataModel(ServiceConfigModel):
    image: Annotated[
        str | None,
        Field(
            examples=["ayon/ftrack-addon-leecher:2.0.0"],
        ),
    ] = None


class ServiceModel(OPModel):
    name: str = Field(...)
    hostname: str = Field(..., examples=["worker03"])
    addon_name: str = Field(..., examples=["ftrack"])
    addon_version: str = Field(..., examples=["2.0.0"])
    service: str = Field(..., examples=["leecher"])
    should_run: bool = Field(...)
    is_running: bool = Field(...)
    last_seen: datetime | None = Field(None)
    data: ServiceDataModel = Field(default_factory=ServiceDataModel)
