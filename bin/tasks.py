"""
Module bin\tasks.py
"""

from celery import shared_task


@shared_task
def bin_test():
    """Simple test task placed in the repo-level `bin` package."""
    print("bin task executed")
