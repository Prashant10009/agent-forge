import argparse
import sys
from typing import List, Optional

class TodoItem:
    def __init__(self, id: int, text: str, completed: bool = False):
        self.id = id
        self.text = text
        self.completed = completed

    def __str__(self):
        status = "[x]" if self.completed else "[ ]"
        return f"{self.id}. {status} {self.text}"

class TodoApp:
    def __init__(self):
        self.todos: List[TodoItem] = []
        self.next_id = 1

    def add(self, text: str) -> TodoItem:
        item = TodoItem(self.next_id, text)
        self.todos.append(item)
        self.next_id += 1
        return item

    def list(self, show_all: bool = False) -> List[TodoItem]:
        if show_all:
            return self.todos
        return [item for item in self.todos if not item.completed]

    def complete(self, id: int) -> Optional[TodoItem]:
        for item in self.todos:
            if item.id == id:
                item.completed = True
                return item
        return None

    def delete(self, id: int) -> Optional[TodoItem]:
        for i, item in enumerate(self.todos):
            if item.id == id:
                return self.todos.pop(i)
        return None

def main():
    parser = argparse.ArgumentParser(description="Simple Todo App")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new todo item")
    add_parser.add_argument("text", help="Text of the todo item")

    # List command
    list_parser = subparsers.add_parser("list", help="List todo items")
    list_parser.add_argument("-a", "--all", action="store_true", help="Show all items including completed")

    # Complete command
    complete_parser = subparsers.add_parser("complete", help="Mark a todo item as completed")
    complete_parser.add_argument("id", type=int, help="ID of the todo item to complete")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a todo item")
    delete_parser.add_argument("id", type=int, help="ID of the todo item to delete")

    args = parser.parse_args()
    app = TodoApp()

    # In a real app, you'd load from persistent storage here

    if args.command == "add":
        item = app.add(args.text)
        print(f"Added: {item}")
    elif args.command == "list":
        items = app.list(not args.all)
        if not items:
            print("No todo items found")
        for item in items:
            print(item)
    elif args.command == "complete":
        item = app.complete(args.id)
        if item:
            print(f"Completed: {item}")
        else:
            print(f"No todo item found with ID {args.id}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "delete":
        item = app.delete(args.id)
        if item:
            print(f"Deleted: {item}")
        else:
            print(f"No todo item found with ID {args.id}", file=sys.stderr)
            sys.exit(1)

    # In a real app, you'd save to persistent storage here

if __name__ == "__main__":
    main()