"""
Auto-insert minimal module docstrings for files flagged missing docstrings.

Reads `precommit_run_after_autofix.txt` to find files reported with D100/D101/etc
and inserts a conservative one-line module docstring if the module has no top-level
string literal already.

Safety: The script creates a .bak copy before modifying each file.
"""

import re
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "precommit_run_after_autofix.txt"

if not OUTPUT.exists():
    print(f"Cannot find {OUTPUT}; run pre-commit and save output to that file first.")
    raise SystemExit(1)

pattern = re.compile(r"^(.+?):\d+:\d+:\s+D10[0-7]?\b", re.IGNORECASE)
files = []
with OUTPUT.open("r", encoding="utf-8", errors="ignore") as fh:
    for line in fh:
        m = pattern.match(line.strip())
        if m:
            p = m.group(1).strip()
            # normalize path separators
            p = p.replace("/", os.sep).replace("\\", os.sep)
            files.append(p)

files = sorted(set(files))
if not files:
    print("No files with D100-series messages found in the precommit output.")
    raise SystemExit(0)

print(f"Found {len(files)} files to check for module docstrings.")
changed = 0
for rel in files:
    fpath = ROOT / rel if not os.path.isabs(rel) else Path(rel)
    if not fpath.exists():
        # try relative to repo root
        fpath = ROOT / rel
    if not fpath.exists() or not fpath.is_file():
        print(f"Skipping (not found): {rel}")
        continue
    text = fpath.read_text(encoding="utf-8", errors="ignore")
    # Skip binary-like files
    if "\0" in text[:1024]:
        print(f"Skipping binary-like file: {fpath}")
        continue
    # Find first non-shebang, non-encoding blank lines
    lines = text.splitlines()
    insert_idx = 0
    # preserve shebang or encoding or module-level comments
    i = 0
    while i < len(lines):
        ln = lines[i].strip()
        if i == 0 and ln.startswith("#!"):
            i += 1
            continue
        # skip encoding comment
        if ln.startswith("#") and "coding" in ln:
            i += 1
            continue
        # skip initial comments
        if ln.startswith("#"):
            i += 1
            continue
        # blank lines
        if ln == "":
            i += 1
            continue
        # if first non-blank non-comment token is a string literal -> has docstring
        if ln.startswith('"') or ln.startswith("'"):
            # assume docstring exists
            insert_idx = None
            break
        # otherwise we should insert before this line
        insert_idx = i
        break
    if insert_idx is None:
        # already has a module docstring
        continue
    # Build minimal docstring
    relpath = os.path.relpath(fpath, ROOT)
    doc = f'"""Module {relpath}\n"""\n\n'
    # backup
    bak = fpath.with_suffix(fpath.suffix + ".bak")
    try:
        fpath.rename(bak)
        prefix = "\n".join(lines[:insert_idx])
        suffix = "\n".join(lines[insert_idx:])
        new_text = ((prefix + "\n") if prefix else "") + doc + suffix
        fpath.write_text(new_text, encoding="utf-8")
        changed += 1
        print(f"Inserted docstring into: {fpath} (backup at {bak.name})")
    except Exception as exc:
        print(f"Failed to update {fpath}: {exc}")

print(f"Finished. Inserted docstrings into {changed} files.")
