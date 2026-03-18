from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SnapshotCommand:
    description: str
    before: dict[str, Any]
    after: dict[str, Any]


class HistoryManager:
    def __init__(self):
        self._undo_stack: list[SnapshotCommand] = []
        self._redo_stack: list[SnapshotCommand] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def push(self, command: SnapshotCommand):
        self._undo_stack.append(command)
        self._redo_stack.clear()

    def pop_undo(self) -> SnapshotCommand | None:
        if not self._undo_stack:
            return None
        return self._undo_stack.pop()

    def push_redo(self, command: SnapshotCommand):
        self._redo_stack.append(command)

    def pop_redo(self) -> SnapshotCommand | None:
        if not self._redo_stack:
            return None
        return self._redo_stack.pop()

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()
