import json
from dataclasses import dataclass, asdict
from typing import List, Optional
import os

@dataclass
class TodoItem:
    title: str
    completed: bool = False

class TodoStorage:
    def __init__(self, file_path: str = "todos.json"):
        self.file_path = file_path

    def save(self, todos: List[TodoItem]) -> None:
        with open(self.file_path, 'w') as f:
            json.dump([asdict(todo) for todo in todos], f)

    def load(self) -> List[TodoItem]:
        if not os.path.exists(self.file_path):
            return []
        
        with open(self.file_path, 'r') as f:
            data = json.load(f)
            return [TodoItem(**item) for item in data]

    def clear(self) -> None:
        if os.path.exists(self.file_path):
            os.remove(self.file_path)