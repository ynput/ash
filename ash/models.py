__all__ = ["OPModel", "Field"]

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


def camelize(src: str) -> str:
    """Convert snake_case to camelCase."""
    components = src.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class OPModel(BaseModel):
    """Base API model."""

    class Config:
        """API model config."""

        orm_mode = True
        allow_population_by_field_name = True
        alias_generator = camelize
        json_loads = json.loads
        json_dumps = json.dumps


class ServiceConfigModel(OPModel):
    volumes: list[str] | None = Field(None, title="Volumes", examples=[["/tmp:/tmp"]])
    ports: list[str] | None = Field(None, title="Ports", examples=[["8080:8080"]])
    mem_limit: str | None = Field(None, title="Memory Limit", examples=["1g"])
    user: str | None = Field(None, title="User", examples=["1000"])
    env: dict[str, Any] = Field(default_factory=dict)


class ServiceDataModel(ServiceConfigModel):
    image: str | None = Field(None, examples=["ayon/ftrack-addon-leecher:2.0.0"])


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
