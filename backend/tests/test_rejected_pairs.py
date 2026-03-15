"""Tests for TASK-015: rejected pairs when removing projects from auto-groups."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import GroupContext, GroupSource
from app.repositories.group import GroupRepo
from app.schemas.group import GroupProjectItem, GroupRead
from app.services.group import GroupService


def _make_project(group_id: uuid.UUID | None = None) -> MagicMock:
    p = MagicMock()
    p.id = uuid.uuid4()
    p.title = "Project"
    p.group_id = group_id
    p.group = None
    return p


def _make_group(source: GroupSource, projects: list) -> MagicMock:
    g = MagicMock()
    g.id = uuid.uuid4()
    g.name = "Test Group"
    g.description = None
    g.source = source
    g.context = GroupContext.main
    g.is_confirmed = False
    g.created_at = datetime.now(timezone.utc)
    g.updated_at = datetime.now(timezone.utc)
    g.projects = projects
    return g


def _make_group_read(group: MagicMock) -> GroupRead:
    return GroupRead(
        id=group.id,
        name=group.name,
        description=group.description,
        source=group.source,
        context=group.context,
        is_confirmed=group.is_confirmed,
        created_at=group.created_at,
        updated_at=group.updated_at,
        projects=[GroupProjectItem(id=p.id, title="P") for p in group.projects],
    )


@pytest.mark.asyncio
async def test_remove_project_from_auto_group_saves_rejected_pairs():
    """Removing a project from auto-group should save rejected pairs."""
    p1 = _make_project()
    p2 = _make_project()
    p3 = _make_project()
    auto_group = _make_group(GroupSource.auto, [p1, p2, p3])
    updated_group = _make_group(GroupSource.auto, [p2, p3])

    svc = GroupService.__new__(GroupService)
    svc.repo = AsyncMock(spec=GroupRepo)
    svc.repo.get_by_id = AsyncMock(side_effect=[auto_group, updated_group])
    svc.repo.save_rejected_pairs_for_removal = AsyncMock()
    svc.repo.remove_project = AsyncMock(return_value=True)

    result = await svc.remove_project(auto_group.id, p1.id)

    svc.repo.save_rejected_pairs_for_removal.assert_called_once_with(
        p1.id, [p2.id, p3.id]
    )
    assert isinstance(result, GroupRead)


@pytest.mark.asyncio
async def test_remove_project_from_manual_group_no_rejected_pairs():
    """Removing a project from manual group should NOT save rejected pairs."""
    p1 = _make_project()
    p2 = _make_project()
    manual_group = _make_group(GroupSource.manual, [p1, p2])
    updated_group = _make_group(GroupSource.manual, [p2])

    svc = GroupService.__new__(GroupService)
    svc.repo = AsyncMock(spec=GroupRepo)
    svc.repo.get_by_id = AsyncMock(side_effect=[manual_group, updated_group])
    svc.repo.save_rejected_pairs_for_removal = AsyncMock()
    svc.repo.remove_project = AsyncMock(return_value=True)

    await svc.remove_project(manual_group.id, p1.id)

    svc.repo.save_rejected_pairs_for_removal.assert_not_called()


@pytest.mark.asyncio
async def test_delete_auto_group_saves_all_pairs():
    """Deleting auto-group saves all within-group pairs as rejected."""
    p1 = _make_project()
    p2 = _make_project()
    p3 = _make_project()
    auto_group = _make_group(GroupSource.auto, [p1, p2, p3])

    svc = GroupService.__new__(GroupService)
    svc.repo = AsyncMock(spec=GroupRepo)
    svc.repo.get_by_id = AsyncMock(return_value=auto_group)
    svc.repo.save_rejected_pairs_for_group = AsyncMock()
    svc.repo.delete = AsyncMock(return_value=True)

    await svc.delete_group(auto_group.id)

    svc.repo.save_rejected_pairs_for_group.assert_called_once_with(
        [p1.id, p2.id, p3.id]
    )


@pytest.mark.asyncio
async def test_delete_manual_group_no_rejected_pairs():
    """Deleting manual group should NOT save rejected pairs."""
    p1 = _make_project()
    p2 = _make_project()
    manual_group = _make_group(GroupSource.manual, [p1, p2])

    svc = GroupService.__new__(GroupService)
    svc.repo = AsyncMock(spec=GroupRepo)
    svc.repo.get_by_id = AsyncMock(return_value=manual_group)
    svc.repo.save_rejected_pairs_for_group = AsyncMock()
    svc.repo.delete = AsyncMock(return_value=True)

    await svc.delete_group(manual_group.id)

    svc.repo.save_rejected_pairs_for_group.assert_not_called()


@pytest.mark.asyncio
async def test_save_rejected_pairs_for_removal_creates_pairs():
    """GroupRepo method creates correct pairs."""
    session = AsyncMock()
    session.add_all = MagicMock()
    repo = GroupRepo(session)

    removed_id = uuid.uuid4()
    other_ids = [uuid.uuid4(), uuid.uuid4()]

    await repo.save_rejected_pairs_for_removal(removed_id, other_ids)

    session.add_all.assert_called_once()
    pairs = session.add_all.call_args[0][0]
    assert len(pairs) == 2
    assert all(p.project_a_id == removed_id for p in pairs)


@pytest.mark.asyncio
async def test_save_rejected_pairs_for_group_all_combinations():
    """GroupRepo saves all combinations for group deletion."""
    session = AsyncMock()
    session.add_all = MagicMock()
    repo = GroupRepo(session)

    project_ids = [uuid.uuid4() for _ in range(4)]
    await repo.save_rejected_pairs_for_group(project_ids)

    session.add_all.assert_called_once()
    pairs = session.add_all.call_args[0][0]
    # C(4,2) = 6 pairs
    assert len(pairs) == 6


@pytest.mark.asyncio
async def test_save_rejected_pairs_empty_no_call():
    """No pairs added when group has no other projects."""
    session = AsyncMock()
    session.add_all = MagicMock()
    repo = GroupRepo(session)

    await repo.save_rejected_pairs_for_removal(uuid.uuid4(), [])
    session.add_all.assert_not_called()

    await repo.save_rejected_pairs_for_group([uuid.uuid4()])
    session.add_all.assert_not_called()
