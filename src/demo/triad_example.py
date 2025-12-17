#!/usr/bin/env python3
"""
A simple CLI demo that prints a greeting and current working directory.
"""

import argparse
import os
import sys
from typing import Optional


def get_greeting(name: Optional[str] = None) -> str:
    """Generate a personalized greeting.
    
    Args:
        name: Optional name to include in greeting. If None, uses generic greeting.
    
    Returns:
        A string containing the greeting message.
    """
    if name:
        return f"Hello, {name}!"
    return "Hello there!"


def get_current_directory() -> str:
    """Get the current working directory.
    
    Returns:
        A string containing the absolute path of the current working directory.
    """
    return os.getcwd()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Triad CLI Demo")
    parser.add_argument(
        "--name",
        type=str,
        help="Optional name for personalized greeting",
        default=None,
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for the CLI application."""
    args = parse_args()
    
    greeting = get_greeting(args.name)
    directory = get_current_directory()
    
    print(greeting)
    print(f"Current directory: {directory}")


if __name__ == "__main__":
    main()