"""Make hw1/NTsik0/src importable as top-level modules when running `pytest hw1/NTsik0`."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
