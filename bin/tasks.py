"""
Module bin\tasks.py
"""

from celery import shared_task  # type: ignore[import-untyped]


@shared_task  # type: ignore[misc]
def bin_test() -> None:
    """Simple test task placed in the repo-level `bin` package."""
    print("bin task executed")
