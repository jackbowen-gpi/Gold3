"""
Compatibility shim for legacy imports that expect a top-level
`bin_functions` module. Re-exports the implementation from
`gchub_db.bin.bin_functions`.
"""

from bin import bin_functions as _bf

__all__ = [n for n in dir(_bf) if not n.startswith("_")]

for _name in __all__:
    globals()[_name] = getattr(_bf, _name)
