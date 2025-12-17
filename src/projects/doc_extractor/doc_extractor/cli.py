import argparse
import json
import sys
from typing import Optional, Dict, Any

from doc_extractor.core import process_document


def main():
    parser = argparse.ArgumentParser(
        description="Document extraction and classification tool"
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the document file (PDF or image)"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output"
    )

    args = parser.parse_args()

    try:
        result = process_document(args.file_path)
        if args.pretty:
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps(result))
    except Exception as e:
        print(f"Error processing document: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()