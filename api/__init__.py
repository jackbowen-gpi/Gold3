"""Local `api` package shim to support legacy imports during development.

This package exposes a minimal `settings` module so code doing
`import api.settings` will succeed while running locally.
"""

__all__ = ["settings"]
