from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json
import os


@dataclass
class Task:
    title: str
    description: str = ""
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        return cls(
            title=data["title"],
            description=data.get("description", ""),
            completed=data.get("completed", False),
            created_at=datetime.fromisoformat(data["created_at"]),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None
        )


class TaskStorage:
    def __init__(self, file_path: str = "tasks.json"):
        self.file_path = file_path
        self.tasks: List[Task] = []
        self.load()

    def add(self, task: Task) -> None:
        self.tasks.append(task)
        self.save()

    def remove(self, task_index: int) -> None:
        if 0 <= task_index < len(self.tasks):
            del self.tasks[task_index]
            self.save()

    def update(self, task_index: int, updated_task: Task) -> None:
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index] = updated_task
            self.save()

    def get_all(self) -> List[Task]:
        return self.tasks

    def save(self) -> None:
        with open(self.file_path, "w") as f:
            json.dump([task.to_dict() for task in self.tasks], f)

    def load(self) -> None:
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                try:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(task_data) for task_data in data]
                except json.JSONDecodeError:
                    self.tasks = []
        else:
            self.tasks = []

    def clear(self) -> None:
        self.tasks = []
        self.save()