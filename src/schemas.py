from typing import Any
from pydantic import BaseModel, Field, field_validator


class JobCreate(BaseModel):
    type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Job identifier",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Job execution payload",
    )

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Job type cannot be empty or whitespace only")
        return cleaned


class JobResponse(BaseModel):
    job_id: int
    status: str