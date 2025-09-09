"""Restore .bak backups created by the convert_tests_to_factories codemod.

Usage:
    python scripts/restore_bak.py path/to/file.py

This will look for a .bak file (same suffix) and restore it over the target.
"""

import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python scripts/restore_bak.py path/to/file.py")
    raise SystemExit(1)

p = Path(sys.argv[1])
if not p.exists():
    print("Target does not exist:", p)
    raise SystemExit(1)

bak = p.with_suffix(f"{p.suffix}.bak")
if not bak.exists():
    print("No backup found:", bak)
    raise SystemExit(1)

print("Restoring", bak, "->", p)
p.write_text(bak.read_text(encoding="utf-8"), encoding="utf-8")
print("Restored.")
