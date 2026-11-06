"""
Historical occurrence ingestion and deduplication module.
Authority: final/feature-specs/05-data-layer.md §4.4, phase-plan.md §4.6, data-foundation.md §2.1.

Ingests historical occurrence records (plant clinic archives, extension surveys)
with verification tier, event date vs report date ordering, source link provenance,
and deterministic deduplication history.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from typing import Any, Dict, List, Optional, Union
import uuid

ALLOWED_VERIFICATION_TIERS = {
    "confirmed",
    "probable",
    "unverified",
    "rejected",
    "historical_clinic",
    "survey",
}


class HistoricalOccurrenceRecord:
    """Represents a validated historical disease or pest occurrence record."""

    def __init__(
        self,
        crop_code: str,
        target_code: str,
        geo_code: str,
        boundary_version: str,
        verification_tier: str,
        event_date: Union[datetime.date, str],
        report_date: Union[datetime.date, str],
        source_link: str,
        source_dataset: str,
        external_accession_id: str,
        severity: Optional[str] = None,
        evidence_summary: Optional[str] = None,
        notes: Optional[str] = None,
        dedupe_history: Optional[List[Dict[str, Any]]] = None,
        is_demo: bool = True,
        record_id: Optional[str] = None,
    ):
        if not crop_code:
            raise ValueError("crop_code cannot be empty")
        if not target_code:
            raise ValueError("target_code cannot be empty")
        if not geo_code:
            raise ValueError("geo_code cannot be empty")
        if not boundary_version:
            raise ValueError("boundary_version cannot be empty")
        if verification_tier not in ALLOWED_VERIFICATION_TIERS:
            raise ValueError(
                f"Invalid verification_tier '{verification_tier}'. "
                f"Must be one of {ALLOWED_VERIFICATION_TIERS}"
            )
        if not source_link:
            raise ValueError("source_link cannot be empty (provenance requirement)")
        if not source_dataset:
            raise ValueError("source_dataset cannot be empty")
        if not external_accession_id:
            raise ValueError("external_accession_id cannot be empty for deduplication")

        self.event_date = self._parse_date(event_date)
        self.report_date = self._parse_date(report_date)

        # Enforce invariant: report_date cannot be earlier than event_date
        if self.report_date < self.event_date:
            raise ValueError(
                f"Temporal violation: report_date ({self.report_date}) is earlier than event_date ({self.event_date})"
            )

        self.id = record_id or str(uuid.uuid4())
        self.crop_code = crop_code
        self.target_code = target_code
        self.geo_code = geo_code
        self.boundary_version = boundary_version
        self.verification_tier = verification_tier
        self.source_link = source_link
        self.source_dataset = source_dataset
        self.external_accession_id = external_accession_id
        self.severity = severity
        self.evidence_summary = evidence_summary
        self.notes = notes
        self.is_demo = is_demo
        self.dedupe_history = dedupe_history or []

        # Deterministic deduplication key computation
        self.dedupe_key = self._compute_dedupe_key()

    @staticmethod
    def _parse_date(val: Union[datetime.date, str]) -> datetime.date:
        if isinstance(val, datetime.date):
            return val
        return datetime.date.fromisoformat(val)

    def _compute_dedupe_key(self) -> str:
        """Computes deterministic SHA-256 dedupe key based on core occurrence coordinates."""
        key_content = (
            f"{self.crop_code}|{self.target_code}|{self.geo_code}|"
            f"{self.event_date.isoformat()}|{self.source_dataset}|{self.external_accession_id}"
        )
        return f"sha256:{hashlib.sha256(key_content.encode('utf-8')).hexdigest()}"

    def register_duplicate(self, duplicate_accession: str, duplicate_source: str, match_reason: str):
        """Records merged duplicate occurrence in the dedupe history log."""
        self.dedupe_history.append({
            "matched_accession": duplicate_accession,
            "matched_source": duplicate_source,
            "matched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "reason": match_reason,
            "resolution": "merged_into_canonical_record",
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "crop_code": self.crop_code,
            "target_code": self.target_code,
            "geo_code": self.geo_code,
            "boundary_version": self.boundary_version,
            "verification_tier": self.verification_tier,
            "event_date": self.event_date.isoformat(),
            "report_date": self.report_date.isoformat(),
            "source_link": self.source_link,
            "source_dataset": self.source_dataset,
            "dedupe_key": self.dedupe_key,
            "dedupe_history": self.dedupe_history,
            "severity": self.severity,
            "evidence_summary": self.evidence_summary,
            "notes": self.notes,
            "is_demo": self.is_demo,
        }
