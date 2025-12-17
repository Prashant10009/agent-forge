import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[2] / 'src' / 'projects' / 'doc_extractor'
sys.path.insert(0, str(ROOT))

from doc_extractor.cli import parse_args, main as cli_main


def test_parse_args_empty():
    """Test parse_args with no arguments."""
    with pytest.raises(SystemExit):
        parse_args([])


def test_parse_args_help():
    """Test help argument."""
    with pytest.raises(SystemExit):
        parse_args(["--help"])


def test_parse_args_input_output():
    """Test input and output arguments."""
    args = parse_args(["--input", "in.txt", "--output", "out.txt"])
    assert args.input == "in.txt"
    assert args.output == "out.txt"


def test_parse_args_verbose():
    """Test verbose flag."""
    args = parse_args(["--input", "in.txt", "--verbose"])
    assert args.verbose is True


def test_parse_args_minimal():
    """Test minimal arguments."""
    args = parse_args(["input.txt"])
    assert args.input == "input.txt"
    assert args.output is None
    assert not args.verbose


def test_parse_args_full():
    """Test all arguments together."""
    args = parse_args(["input.txt", "--output", "output.txt", "--verbose"])
    assert args.input == "input.txt"
    assert args.output == "output.txt"
    assert args.verbose


@patch('doc_extractor.cli.process_file')
def test_cli_main_success(mock_process):
    """Test CLI main function success case."""
    mock_process.return_value = "success"
    with patch('sys.argv', ['cli.py', '--input', 'in.txt', '--output', 'out.txt']):
        assert cli_main() == 0


@patch('doc_extractor.cli.process_file')
def test_cli_main_failure(mock_process):
    """Test CLI main function error case."""
    mock_process.side_effect = ValueError("Test error")
    with patch('sys.argv', ['cli.py', '--input', 'in.txt', '--output', 'out.txt']):
        assert cli_main() == 1


@patch('doc_extractor.cli.parse_args')
def test_cli_main_missing_args(mock_parse):
    """Test CLI main with missing required args."""
    mock_parse.return_value = MagicMock(input=None, output=None)
    with patch('sys.argv', ['cli.py']):
        assert cli_main() == 2


def test_cli_main_minimal_args():
    """Test CLI with minimal arguments."""
    with patch('sys.argv', ['cli.py', 'input.txt']):
        with patch('doc_extractor.cli.process_file') as mock_process:
            cli_main()
            mock_process.assert_called_once_with('input.txt', None, False)


def test_cli_main_full_args():
    """Test CLI with all arguments."""
    with patch('sys.argv', ['cli.py', 'input.txt', '--output', 'output.txt', '--verbose']):
        with patch('doc_extractor.cli.process_file') as mock_process:
            cli_main()
            mock_process.assert_called_once_with('input.txt', 'output.txt', True)