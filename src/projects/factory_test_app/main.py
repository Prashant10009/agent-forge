import sys
from typing import Optional

def greet(name: Optional[str] = None) -> str:
    if name is None:
        return "Hello, World!"
    return f"Hello, {name}!"

def main() -> None:
    name = None
    if len(sys.argv) > 1:
        name = ' '.join(sys.argv[1:])
    print(greet(name))

if __name__ == '__main__':
    main()