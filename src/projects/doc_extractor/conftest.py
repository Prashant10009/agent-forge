import sys
from pathlib import Path

# This file lives in: src/projects/doc_extractor/conftest.py
# So its parent is:   src/projects/doc_extractor
PROJECT_ROOT = Path(__file__).resolve().parent

# This folder contains the 'doc_extractor' package directory,
# so we add it to sys.path so imports like `from doc_extractor.cli import ...` work.
project_root_str = str(PROJECT_ROOT)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)
