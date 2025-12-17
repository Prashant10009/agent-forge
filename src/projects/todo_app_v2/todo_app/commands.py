import argparse
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Task:
    id: int
    description: str
    completed: bool


class TodoApp:
    def __init__(self):
        self.tasks: List[Task] = []
        self.next_id = 1

    def add_task(self, description: str) -> Task:
        task = Task(id=self.next_id, description=description, completed=False)
        self.tasks.append(task)
        self.next_id += 1
        return task

    def complete_task(self, task_id: int) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                task.completed = True
                return task
        return None

    def list_tasks(self) -> List[Task]:
        return sorted(self.tasks, key=lambda t: t.id)


def add_command(args, todo_app: TodoApp) -> None:
    task = todo_app.add_task(args.description)
    print(f"Added task #{task.id}: {task.description}")


def complete_command(args, todo_app: TodoApp) -> None:
    task = todo_app.complete_task(args.task_id)
    if task:
        print(f"Completed task #{task.id}: {task.description}")
    else:
        print(f"Task #{args.task_id} not found")


def list_command(args, todo_app: TodoApp) -> None:
    tasks = todo_app.list_tasks()
    if not tasks:
        print("No tasks found")
        return

    for task in tasks:
        status = "✓" if task.completed else " "
        print(f"{task.id}. [{status}] {task.description}")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Todo App")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("description", help="Task description")

    # Complete command
    complete_parser = subparsers.add_parser("complete", help="Mark task as complete")
    complete_parser.add_argument("task_id", type=int, help="Task ID to complete")

    # List command
    subparsers.add_parser("list", help="List all tasks")

    return parser


def main():
    todo_app = TodoApp()
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "add":
        add_command(args, todo_app)
    elif args.command == "complete":
        complete_command(args, todo_app)
    elif args.command == "list":
        list_command(args, todo_app)


if __name__ == "__main__":
    main()