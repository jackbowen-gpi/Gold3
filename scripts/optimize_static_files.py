#!/usr/bin/env python
"""
Static File Optimization Utilities

This script provides utilities for optimizing static file serving in production.
Run this script to prepare static files for production deployment.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings
from django.core.management import execute_from_command_line


def main():
    """Main function to run static file optimizations."""
    print("=== Django Static File Optimization Utility ===\n")

    # Check if static root exists
    static_root = getattr(settings, "STATIC_ROOT", None)
    if not static_root:
        print("ERROR: STATIC_ROOT is not configured in settings")
        return 1

    static_path = Path(static_root)
    if not static_path.exists():
        print(f"WARNING: STATIC_ROOT directory does not exist: {static_root}")
        print("Run 'python manage.py collectstatic' first")
        return 1

    print(f"Static root: {static_root}")
    print(f"Static URL: {getattr(settings, 'STATIC_URL', '/static/')}")
    cache_timeout = getattr(settings, "STATIC_CACHE_TIMEOUT", 31536000)
    print(f"Cache timeout: {cache_timeout} seconds")
    print()

    # Run collectstatic to ensure all static files are collected
    print("1. Collecting static files...")
    try:
        execute_from_command_line(["manage.py", "collectstatic", "--noinput", "--clear"])
        print("✓ Static files collected successfully")
    except Exception as e:
        print(f"✗ Error collecting static files: {e}")
        return 1

    # Run optimization command
    print("\n2. Optimizing static files...")
    try:
        # Import and run our optimization logic directly
        from gchub_db.management.commands.optimize_static import (
            Command as OptimizeCommand,
        )

        optimize_cmd = OptimizeCommand()
        # Run compression
        optimize_cmd.handle(compress=True, generate_manifest=True, dry_run=False, **{})
        print("✓ Static files optimized successfully")
    except Exception as e:
        print(f"✗ Error optimizing static files: {e}")
        return 1

    # Display optimization results
    print("\n3. Optimization Results:")
    compressed_files = list(static_path.rglob("*.gz"))
    manifest_file = static_path / "static-manifest.json"

    print(f"  - Compressed files: {len(compressed_files)}")
    print(f"  - Manifest file: {'✓' if manifest_file.exists() else '✗'}")

    # Count total static files
    total_files = sum(1 for _ in static_path.rglob("*") if _.is_file())
    print(f"  - Total static files: {total_files}")

    print("\n=== Optimization Complete ===")
    print("\nNext steps for production:")
    print("1. Configure your web server (nginx/apache) to serve static files")
    print("2. Set up CDN if using one (update STATIC_URL_CDN in settings)")
    print("3. Enable gzip compression in your web server")
    print("4. Test static file serving and caching")

    return 0


if __name__ == "__main__":
    sys.exit(main())
