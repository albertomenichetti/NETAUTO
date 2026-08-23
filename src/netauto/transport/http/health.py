"""Health HTTP wire DTOs."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from netauto.health import HealthStatus


class ComponentHealthDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: HealthStatus
    message: str | None = None


class CoreHealthDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app_status: ComponentHealthDTO
    db_status: ComponentHealthDTO
    execution_time_ms: Annotated[int, Field(ge=0)]
