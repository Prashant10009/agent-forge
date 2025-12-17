import unittest
from unittest.mock import patch, MagicMock
from projects.todo_app_v2.commands import (
    AddCommand,
    ListCommand,
    CompleteCommand,
    DeleteCommand
)

class TestAddCommand(unittest.TestCase):
    def test_execute_adds_task(self):
        mock_storage = MagicMock()
        cmd = AddCommand(mock_storage, "Buy milk")
        cmd.execute()
        mock_storage.add_task.assert_called_once_with("Buy milk")

class TestListCommand(unittest.TestCase):
    def test_execute_lists_tasks(self):
        mock_storage = MagicMock()
        mock_storage.get_tasks.return_value = [
            {"id": 1, "description": "Task 1", "completed": False},
            {"id": 2, "description": "Task 2", "completed": True}
        ]
        cmd = ListCommand(mock_storage)
        
        with patch('builtins.print') as mock_print:
            cmd.execute()
            
        mock_storage.get_tasks.assert_called_once()
        self.assertEqual(mock_print.call_count, 2)

class TestCompleteCommand(unittest.TestCase):
    def test_execute_completes_task(self):
        mock_storage = MagicMock()
        cmd = CompleteCommand(mock_storage, 1)
        cmd.execute()
        mock_storage.complete_task.assert_called_once_with(1)

    def test_execute_invalid_id(self):
        mock_storage = MagicMock()
        mock_storage.complete_task.side_effect = ValueError("Invalid task ID")
        cmd = CompleteCommand(mock_storage, 99)
        
        with patch('builtins.print') as mock_print:
            cmd.execute()
            
        mock_print.assert_called_once_with("Error: Invalid task ID")

class TestDeleteCommand(unittest.TestCase):
    def test_execute_deletes_task(self):
        mock_storage = MagicMock()
        cmd = DeleteCommand(mock_storage, 1)
        cmd.execute()
        mock_storage.delete_task.assert_called_once_with(1)

    def test_execute_invalid_id(self):
        mock_storage = MagicMock()
        mock_storage.delete_task.side_effect = ValueError("Invalid task ID")
        cmd = DeleteCommand(mock_storage, 99)
        
        with patch('builtins.print') as mock_print:
            cmd.execute()
            
        mock_print.assert_called_once_with("Error: Invalid task ID")

if __name__ == '__main__':
    unittest.main()