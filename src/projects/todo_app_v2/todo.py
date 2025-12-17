import argparse
import sys
from typing import List, Optional

class TodoItem:
    def __init__(self, title: str, completed: bool = False):
        self.title = title
        self.completed = completed

    def __str__(self):
        status = "[x]" if self.completed else "[ ]"
        return f"{status} {self.title}"

class TodoApp:
    def __init__(self):
        self.todos: List[TodoItem] = []

    def add(self, title: str) -> None:
        self.todos.append(TodoItem(title))

    def list(self) -> List[TodoItem]:
        return self.todos

def main():
    app = TodoApp()
    
    parser = argparse.ArgumentParser(description="Simple Todo App")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new todo item")
    add_parser.add_argument("title", help="Title of the todo item")

    # List command
    list_parser = subparsers.add_parser("list", help="List all todo items")

    args = parser.parse_args()

    if args.command == "add":
        app.add(args.title)
        print(f"Added: {args.title}")
    elif args.command == "list":
        todos = app.list()
        if not todos:
            print("No todos yet!")
        else:
            for i, todo in enumerate(todos, 1):
                print(f"{i}. {todo}")

if __name__ == "__main__":
    main()