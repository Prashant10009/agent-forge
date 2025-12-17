import json
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path


def read_json_file(file_path: Path) -> Dict[str, Any]:
    """Read JSON file and return its content as dictionary."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json_file(file_path: Path, data: Dict[str, Any]) -> None:
    """Write dictionary data to JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dictionaries with dict2 taking precedence."""
    return {**dict1, **dict2}


@dataclass
class Config:
    """Base configuration dataclass."""
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        return cls(**data)


def validate_path(path: Path, must_exist: bool = False) -> bool:
    """Validate a path with optional existence check."""
    if must_exist:
        return path.exists()
    return True


def filter_list(items: List[Any], condition: Any) -> List[Any]:
    """Filter a list based on a condition."""
    return [item for item in items if condition(item)]


def get_unique_items(items: List[Any]) -> List[Any]:
    """Return a list of unique items preserving order."""
    seen = set()
    return [item for item in items if not (item in seen or seen.add(item))]


def format_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"