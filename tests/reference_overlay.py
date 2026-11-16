"""In-memory mutations of existing Skill files for structural regression tests."""
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch


class ReferenceOverlay:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.changes = {}
        self.stack = ExitStack()

    def __enter__(self):
        original = {name: getattr(Path, name) for name in
                    ("read_bytes", "read_text", "write_bytes", "write_text", "unlink", "exists", "is_file", "rglob")}
        changes, root = self.changes, self.root

        def key(path):
            resolved = path.resolve()
            if not resolved.is_relative_to(root):
                raise AssertionError("Test mutation must stay within its virtual Skill")
            return resolved

        def read_bytes(path):
            resolved = path.resolve()
            if resolved in changes:
                if changes[resolved] is None:
                    raise FileNotFoundError(path)
                return changes[resolved]
            return original["read_bytes"](path)

        def read_text(path, encoding=None, errors=None):
            return read_bytes(path).decode(encoding or "utf-8", errors or "strict")

        def write_bytes(path, data):
            changes[key(path)] = bytes(data)
            return len(data)

        def write_text(path, data, encoding=None, errors=None, newline=None):
            write_bytes(path, data.encode(encoding or "utf-8", errors or "strict"))
            return len(data)

        def unlink(path, missing_ok=False):
            changes[key(path)] = None

        def exists(path):
            resolved = path.resolve()
            return changes[resolved] is not None if resolved in changes else original["exists"](path)

        def is_file(path):
            resolved = path.resolve()
            return changes[resolved] is not None if resolved in changes else original["is_file"](path)

        def rglob(path, pattern):
            seen = set()
            for result in original["rglob"](path, pattern):
                seen.add(result.resolve())
                if changes.get(result.resolve(), b"") is not None:
                    yield result
            for result, data in changes.items():
                if data is not None and result not in seen and result.is_relative_to(path.resolve()) and result.match(pattern):
                    yield result

        for name, replacement in (("read_bytes", read_bytes), ("read_text", read_text),
                ("write_bytes", write_bytes), ("write_text", write_text), ("unlink", unlink),
                ("exists", exists), ("is_file", is_file), ("rglob", rglob)):
            self.stack.enter_context(patch.object(Path, name, replacement))
        return self

    def __exit__(self, *exc):
        return self.stack.__exit__(*exc)
