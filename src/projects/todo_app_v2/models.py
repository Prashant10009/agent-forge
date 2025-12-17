from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class TodoItem:
    title: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    def is_completed(self) -> bool:
        return self.completed_at is not None

    def mark_complete(self) -> None:
        if not self.is_completed():
            self.completed_at = datetime.now()

    def mark_incomplete(self) -> None:
        self.completed_at = None


class TodoList:
    def __init__(self) -> None:
        self.items: List[TodoItem] = []

    def add(self, title: str) -> TodoItem:
        item = TodoItem(title=title, created_at=datetime.now())
        self.items.append(item)
        return item

    def list_all(self) -> List[TodoItem]:
        return sorted(self.items, key=lambda x: x.created_at)

    def list_active(self) -> List[TodoItem]:
        return [item for item in self.list_all() if not item.is_completed()]

    def list_completed(self) -> List[TodoItem]:
        return [item for item in self.list_all() if item.is_completed()]

    def find_by_title(self, title: str) -> Optional[TodoItem]:
        for item in self.items:
            if item.title == title:
                return item
        return None