"""
Top-level shim to expose bin functions for tests that `import bin_functions`.

This delegates to the existing implementation under the `bin` package (or
`src` fallback) so tests that expect a top-level module continue to work.
"""

from __future__ import annotations

__all__ = []

_loaded = False
for candidate in ("bin.bin_functions", "src.bin_functions"):
    try:
        module = __import__(candidate, fromlist=["*"])
    except Exception:
        module = None  # type: ignore[assignment]
    if module is not None:
        # Export module attributes at top-level
        for name in dir(module):
            if name.startswith("__"):
                continue
            globals()[name] = getattr(module, name)
            __all__.append(name)
        _loaded = True
        break

if not _loaded:
    raise ImportError("Could not import bin.bin_functions or src.bin_functions; ensure one exists")
