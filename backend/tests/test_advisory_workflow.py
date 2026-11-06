from __future__ import annotations

import pytest
from app.modules.advisories.registry import AdvisoryRegistry, AdvisoryWorkflowError

from tests.support_notifications import (
    NOW,
    QUALIFIED_ACCOUNTS,
    MutableClock,
    make_draft,
    populate_advisory,
)


def approve(registry: AdvisoryRegistry, advisory_id: str, **overrides) -> None:
    values = {
        "version": 1,
        "approver_id": "approver-1",
        "approver_role": "pathologist",
        "qualified_accounts": QUALIFIED_ACCOUNTS,
    }
    values.update(overrides)
    registry.approve(advisory_id, **values)


def test_draft_is_retained_as_an_immutable_version() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    draft = make_draft()

    advisory = registry.create_draft(draft)

    assert advisory.status == "draft"
    assert advisory.current_version == 1
    assert advisory.versions[0].content_hash
    assert advisory.versions[0].author_role == "agronomist"
    assert advisory.approvals == ()


def test_approval_requires_a_second_qualified_person() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    advisory = registry.create_draft(make_draft())

    with pytest.raises(AdvisoryWorkflowError) as caught:
        approve(registry, advisory.advisory_id, approver_id="author-1", approver_role="agronomist")

    assert caught.value.code == "author_cannot_approve"


def test_publication_is_blocked_when_only_one_qualified_account_exists() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    advisory = registry.create_draft(make_draft())

    with pytest.raises(AdvisoryWorkflowError) as caught:
        approve(
            registry,
            advisory.advisory_id,
            qualified_accounts={"author-1": "agronomist"},
        )

    assert caught.value.code == "insufficient_qualified_accounts"


def test_approver_must_be_qualified_and_on_the_roster() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    advisory = registry.create_draft(make_draft())

    with pytest.raises(AdvisoryWorkflowError) as caught:
        approve(registry, advisory.advisory_id, approver_id="outsider-1")
    assert caught.value.code == "approver_not_in_roster"

    with pytest.raises(AdvisoryWorkflowError) as caught:
        approve(registry, advisory.advisory_id, approver_role="editor")
    assert caught.value.code == "approver_not_qualified"


def test_approved_and_published_content_is_retrievable_with_scope_filters() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    advisory_id = populate_advisory(registry)

    result = registry.retrieve(crop="crop-1", target="target-1", geo="area-1", language="en")

    assert result.fallback is None
    assert len(result.items) == 1
    item = result.items[0]
    assert item.advisory_id == advisory_id
    assert item.version == 1
    assert item.approver_role == "pathologist"
    assert not hasattr(item, "author_id")
    assert not hasattr(item, "approver_id")


@pytest.mark.parametrize(
    ("crop", "target", "geo", "language"),
    [
        ("other-crop", "target-1", "area-1", "en"),
        ("crop-1", "other-target", "area-1", "en"),
        ("crop-1", "target-1", "other-area", "en"),
        ("crop-1", "target-1", "area-1", "kn"),
    ],
)
def test_retrieval_never_returns_out_of_scope_content(
    crop: str, target: str, geo: str, language: str
) -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    populate_advisory(registry)

    result = registry.retrieve(crop=crop, target=target, geo=geo, language=language)

    assert result.items == ()
    assert result.fallback is not None
    assert result.fallback.next_step == "request_expert_review"


def test_all_supported_areas_scope_matches_any_area() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    populate_advisory(registry, draft=make_draft(geo_scope=["all_supported_areas"]))

    result = registry.retrieve(crop="crop-1", target="target-1", geo="area-99", language="en")

    assert len(result.items) == 1


def test_expired_content_is_never_served() -> None:
    clock = MutableClock()
    registry = AdvisoryRegistry(clock=clock)
    populate_advisory(registry, draft=make_draft(valid_to=NOW.replace(day=7)))

    assert registry.retrieve(crop="crop-1", target="target-1", geo="area-1", language="en").items

    clock.advance(days=2)

    result = registry.retrieve(crop="crop-1", target="target-1", geo="area-1", language="en")
    assert result.items == ()
    assert result.fallback is not None


def test_publishing_already_expired_content_is_refused() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    advisory = registry.create_draft(
        make_draft(valid_from=NOW.replace(day=1), valid_to=NOW.replace(day=5))
    )
    approve(registry, advisory.advisory_id)

    with pytest.raises(AdvisoryWorkflowError) as caught:
        registry.publish(advisory.advisory_id, version=1, actor_id="publisher-1")

    assert caught.value.code == "advisory_expired"


def test_an_edit_creates_a_new_version_and_clears_approval() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    advisory_id = populate_advisory(registry)
    first_hash = registry.get(advisory_id).versions[0].content_hash  # type: ignore[union-attr]

    updated = registry.create_version(
        advisory_id,
        make_draft(title="Synthetic updated advisory"),
        editor_id="author-1",
    )

    assert updated.status == "draft"
    assert updated.current_version == 2
    assert len(updated.versions) == 2
    assert updated.versions[0].content_hash == first_hash
    assert updated.versions[1].content_hash != first_hash
    assert updated.approval_for(updated.current_version) is None
    assert updated.approval_for(1) is not None
    assert (
        registry.retrieve(crop="crop-1", target="target-1", geo="area-1", language="en").items == ()
    )


def test_withdrawal_removes_every_version_from_retrieval_and_is_audited() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    advisory_id = populate_advisory(registry)

    withdrawn = registry.withdraw(
        advisory_id, actor_id="approver-1", reason="Synthetic safety withdrawal"
    )

    assert withdrawn.status == "withdrawn"
    assert withdrawn.withdrawn_reason == "Synthetic safety withdrawal"
    assert (
        registry.retrieve(crop="crop-1", target="target-1", geo="area-1", language="en").items == ()
    )
    event_types = [event.event_type for event in registry.audit_events()]
    assert "advisory.approved" in event_types
    assert "advisory.published" in event_types
    assert "advisory.withdrawn" in event_types


def test_withdrawal_requires_a_reason() -> None:
    registry = AdvisoryRegistry(clock=MutableClock())
    advisory_id = populate_advisory(registry)

    with pytest.raises(AdvisoryWorkflowError) as caught:
        registry.withdraw(advisory_id, actor_id="approver-1", reason="  ")

    assert caught.value.code == "withdrawal_reason_required"
