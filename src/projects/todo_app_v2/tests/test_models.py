import unittest
from dataclasses import asdict
from datetime import datetime
from src.projects.todo_app_v2.models import TodoItem, TodoList


class TestTodoItem(unittest.TestCase):
    def test_creation(self):
        item = TodoItem(id=1, title="Test", description="Test description")
        self.assertEqual(item.id, 1)
        self.assertEqual(item.title, "Test")
        self.assertEqual(item.description, "Test description")
        self.assertFalse(item.completed)
        self.assertIsInstance(item.created_at, datetime)
        self.assertIsNone(item.completed_at)

    def test_mark_complete(self):
        item = TodoItem(id=1, title="Test")
        item.mark_complete()
        self.assertTrue(item.completed)
        self.assertIsInstance(item.completed_at, datetime)

    def test_mark_incomplete(self):
        item = TodoItem(id=1, title="Test", completed=True)
        item.mark_incomplete()
        self.assertFalse(item.completed)
        self.assertIsNone(item.completed_at)

    def test_to_dict(self):
        item = TodoItem(id=1, title="Test")
        item_dict = asdict(item)
        self.assertEqual(item_dict["id"], 1)
        self.assertEqual(item_dict["title"], "Test")
        self.assertIn("created_at", item_dict)


class TestTodoList(unittest.TestCase):
    def setUp(self):
        self.todo_list = TodoList()
        self.item1 = TodoItem(id=1, title="First")
        self.item2 = TodoItem(id=2, title="Second")

    def test_add_item(self):
        self.todo_list.add_item(self.item1)
        self.assertEqual(len(self.todo_list.items), 1)
        self.assertEqual(self.todo_list.items[0].title, "First")

    def test_remove_item(self):
        self.todo_list.add_item(self.item1)
        self.todo_list.add_item(self.item2)
        self.todo_list.remove_item(1)
        self.assertEqual(len(self.todo_list.items), 1)
        self.assertEqual(self.todo_list.items[0].id, 2)

    def test_find_item(self):
        self.todo_list.add_item(self.item1)
        self.todo_list.add_item(self.item2)
        found = self.todo_list.find_item(2)
        self.assertEqual(found.title, "Second")

    def test_get_completed(self):
        self.item2.mark_complete()
        self.todo_list.add_item(self.item1)
        self.todo_list.add_item(self.item2)
        completed = self.todo_list.get_completed()
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].id, 2)

    def test_get_pending(self):
        self.item2.mark_complete()
        self.todo_list.add_item(self.item1)
        self.todo_list.add_item(self.item2)
        pending = self.todo_list.get_pending()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].id, 1)


if __name__ == "__main__":
    unittest.main()