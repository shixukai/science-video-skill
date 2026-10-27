"""Repository tests use package-qualified discovery to avoid bundled name collisions."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
