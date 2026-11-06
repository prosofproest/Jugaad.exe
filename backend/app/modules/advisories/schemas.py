"""Response models for the advisory retrieval surface."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.modules.advisories.models import AdvisoryFallback, ApprovedAdvisoryView


class AdvisoryQueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ApprovedAdvisoryView] = Field(default_factory=list)
    fallback: AdvisoryFallback | None = None
