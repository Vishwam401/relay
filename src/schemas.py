import hashlib
import json
from typing import Any
from pydantic import BaseModel, Field, field_validator

IDEMPOTENCY_KEY_MAX_LENGTH: int = 128


def request_fingerprint(job_type: str, payload: dict[str, Any] | None) -> str:
    cleaned_type = job_type.strip()
    canonical_payload = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"))
    content = f"{cleaned_type}:{canonical_payload}".encode("utf-8")
    return hashlib.sha256(content).hexdigest().lower()


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
    idempotency_key: str | None = Field(
        default=None,
        description="Optional caller-supplied idempotency key",
    )

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Job type cannot be empty or whitespace only")
        return cleaned

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Idempotency key cannot be empty or whitespace only")
        if len(cleaned) > IDEMPOTENCY_KEY_MAX_LENGTH:
            raise ValueError(
                f"Idempotency key exceeds maximum length of {IDEMPOTENCY_KEY_MAX_LENGTH}"
            )
        return cleaned


class JobResponse(BaseModel):
    job_id: int
    status: str