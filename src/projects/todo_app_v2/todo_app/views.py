from typing import List, Dict, Optional
from dataclasses import dataclass
import sys

@dataclass
class TodoItem:
    id: int
    title: str
    completed: bool

def display_todo_list(todos: List[TodoItem], show_completed: bool = True) -> None:
    """Display the todo list with optional filtering of completed items."""
    if not todos:
        print("No todo items found.")
        return

    print("\nTodo List:")
    print("-" * 40)
    
    for item in todos:
        if not show_completed and item.completed:
            continue
        status = "[x]" if item.completed else "[ ]"
        print(f"{item.id}. {status} {item.title}")
    
    print("-" * 40)
    print(f"Total: {len(todos)} items")
    if not show_completed:
        print("(Completed items hidden)")

def display_single_todo(item: TodoItem) -> None:
    """Display details of a single todo item."""
    if not item:
        print("Todo item not found.")
        return
    
    status = "Completed" if item.completed else "Pending"
    print("\nTodo Item Details:")
    print("-" * 40)
    print(f"ID: {item.id}")
    print(f"Title: {item.title}")
    print(f"Status: {status}")
    print("-" * 40)

def display_error(message: str) -> None:
    """Display an error message to the user."""
    print(f"Error: {message}", file=sys.stderr)

def display_success(message: str) -> None:
    """Display a success message to the user."""
    print(f"Success: {message}")

def display_help() -> None:
    """Display help information about available commands."""
    help_text = """
Todo App Commands:
- list [--all]       : Show todo items (--all shows completed items)
- add <title>        : Add a new todo item
- complete <id>      : Mark an item as completed
- delete <id>        : Delete a todo item
- view <id>          : View details of a todo item
- help               : Show this help message
"""
    print(help_text)