import unittest
import tempfile
import os
from unittest.mock import patch, mock_open
from projects.todo_app_v2.storage import Storage

class TestStorage(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.storage = Storage(self.temp_file.name)

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_add_item(self):
        self.storage.add_item("Test task")
        items = self.storage.get_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['title'], "Test task")
        self.assertTrue(isinstance(items[0]['id'], int))

    def test_get_items_empty(self):
        items = self.storage.get_items()
        self.assertEqual(len(items), 0)

    def test_get_items_multiple(self):
        self.storage.add_item("Task 1")
        self.storage.add_item("Task 2")
        items = self.storage.get_items()
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['title'], "Task 1")
        self.assertEqual(items[1]['title'], "Task 2")

    def test_remove_item(self):
        self.storage.add_item("Task to remove")
        items = self.storage.get_items()
        item_id = items[0]['id']
        
        self.storage.remove_item(item_id)
        items = self.storage.get_items()
        self.assertEqual(len(items), 0)

    def test_remove_nonexistent_item(self):
        with self.assertRaises(ValueError):
            self.storage.remove_item(999)

    def test_persistence(self):
        self.storage.add_item("Persistent task")
        del self.storage
        
        new_storage = Storage(self.temp_file.name)
        items = new_storage.get_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['title'], "Persistent task")

    @patch('builtins.open', mock_open(read_data='[{"id": 1, "title": "Mocked task"}]'))
    def test_load_from_file(self):
        storage = Storage("dummy_path.json")
        items = storage.get_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['title'], "Mocked task")

    @patch('builtins.open', side_effect=IOError("File error"))
    def test_load_file_error(self, mock_file):
        storage = Storage("invalid_path.json")
        items = storage.get_items()
        self.assertEqual(len(items), 0)

if __name__ == '__main__':
    unittest.main()