"""
Management command for static file optimization and cache management.
"""

import gzip
import hashlib
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = "Optimize static files for production deployment"

    def add_arguments(self, parser):
        parser.add_argument(
            "--compress",
            action="store_true",
            help="Compress static files with gzip",
        )
        parser.add_argument(
            "--generate-manifest",
            action="store_true",
            help="Generate cache manifest for static files",
        )
        parser.add_argument(
            "--clear-cache",
            action="store_true",
            help="Clear static file cache",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )

    def handle(self, *args, **options):
        static_root = getattr(settings, "STATIC_ROOT", None)
        if not static_root:
            raise CommandError("STATIC_ROOT is not configured")

        static_path = Path(static_root)
        if not static_path.exists():
            raise CommandError(f"STATIC_ROOT directory does not exist: {static_root}")

        self.stdout.write(f"Processing static files in: {static_root}")

        if options["compress"]:
            self._compress_static_files(static_path, options["dry_run"])

        if options["generate_manifest"]:
            self._generate_manifest(static_path, options["dry_run"])

        if options["clear_cache"]:
            self._clear_cache(options["dry_run"])

        if not any([options["compress"], options["generate_manifest"], options["clear_cache"]]):
            self.stdout.write(self.style.WARNING("No action specified. Use --compress, --generate-manifest, or --clear-cache"))

    def _compress_static_files(self, static_path, dry_run=False):
        """Compress static files with gzip for better performance."""
        self.stdout.write("Compressing static files...")

        compressible_extensions = {
            ".css",
            ".js",
            ".html",
            ".txt",
            ".xml",
            ".json",
            ".svg",
        }
        compressed_count = 0

        for file_path in static_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in compressible_extensions:
                gz_path = file_path.with_suffix(file_path.suffix + ".gz")

                if gz_path.exists():
                    self.stdout.write(f"Skipping (already compressed): {file_path.relative_to(static_path)}")
                    continue

                if dry_run:
                    self.stdout.write(f"Would compress: {file_path.relative_to(static_path)}")
                    compressed_count += 1
                    continue

                try:
                    with open(file_path, "rb") as f_in:
                        with gzip.open(gz_path, "wb", compresslevel=9) as f_out:
                            f_out.writelines(f_in)
                    compressed_count += 1
                    self.stdout.write(f"Compressed: {file_path.relative_to(static_path)}")
                except Exception as e:
                    self.stderr.write(f"Error compressing {file_path}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Compressed {compressed_count} static files"))

    def _generate_manifest(self, static_path, dry_run=False):
        """Generate a manifest of static files with their hashes for cache busting."""
        self.stdout.write("Generating static file manifest...")

        manifest = {}
        file_count = 0

        for file_path in static_path.rglob("*"):
            if file_path.is_file():
                try:
                    with open(file_path, "rb") as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    relative_path = str(file_path.relative_to(static_path))
                    manifest[relative_path] = file_hash
                    file_count += 1
                except Exception as e:
                    self.stderr.write(f"Error processing {file_path}: {e}")

        if dry_run:
            self.stdout.write(f"Would generate manifest with {file_count} files")
            return

        manifest_path = static_path / "static-manifest.json"
        try:
            import json

            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
            self.stdout.write(self.style.SUCCESS(f"Generated manifest with {file_count} files: {manifest_path}"))
        except Exception as e:
            raise CommandError(f"Error writing manifest: {e}")

    def _clear_cache(self, dry_run=False):
        """Clear the static file cache."""
        from django.core.cache import cache

        if dry_run:
            self.stdout.write("Would clear static file cache")
            return

        try:
            # Clear all cache entries with the static file prefix
            cache_key_prefix = getattr(settings, "CACHE_MIDDLEWARE_KEY_PREFIX", "")
            if cache_key_prefix:
                # This is a simplified cache clearing - in production you might want more sophisticated clearing
                cache.clear()
                self.stdout.write(self.style.SUCCESS("Cleared static file cache"))
            else:
                self.stdout.write(self.style.WARNING("No cache key prefix configured, skipping cache clear"))
        except Exception as e:
            raise CommandError(f"Error clearing cache: {e}")
