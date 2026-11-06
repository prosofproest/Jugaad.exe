"""Public advisory retrieval (spec 07 §4, FR-07-03/04).

Only approved, currently valid, in-scope content is returned. When none exists
the response contains a fallback message and an escalation step; generic web or
generated text is never substituted.

There is no public write surface. Drafting, approval, publication and
withdrawal require authenticated roles, which arrive with Phase 2 identity.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.modules.advisories.registry import AdvisoryRegistry
from app.modules.advisories.schemas import AdvisoryQueryResponse
from app.modules.identity.dependencies import get_current_context
from app.modules.identity.service import AuthContext

router = APIRouter(prefix="/advisories", tags=["advisories"])

_registry: AdvisoryRegistry | None = None


def get_advisory_registry() -> AdvisoryRegistry:
    global _registry
    if _registry is None:
        _registry = AdvisoryRegistry()
    return _registry


def set_advisory_registry(registry: AdvisoryRegistry | None) -> None:
    """Test/DI hook. Passing ``None`` restores lazy default construction."""

    global _registry
    _registry = registry


@router.get("", response_model=AdvisoryQueryResponse)
def list_advisories(
    crop: str = Query(..., min_length=1, max_length=80),
    target: str = Query(..., min_length=1, max_length=80),
    geo: str = Query(..., min_length=1, max_length=80),
    language: str = Query(..., min_length=2, max_length=16),
    _context: AuthContext = Depends(get_current_context),
) -> AdvisoryQueryResponse:
    result = get_advisory_registry().retrieve(
        crop=crop,
        target=target,
        geo=geo,
        language=language,
    )
    return AdvisoryQueryResponse(
        items=list(result.items),
        fallback=result.fallback,
    )
