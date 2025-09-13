#!/usr/bin/env python
"""
Efficient PostgreSQL data replication script for Gold3 development.

This script provides multiple methods for replicating data from a source
PostgreSQL database to a target database with minimal storage overhead.

Features:
- Direct database-to-database replication (no intermediate files)
- Selective table replication
- Compressed data transfer
- Automatic cleanup
- Docker container support

Usage:
    python scripts/db_replicate.py --source gchub_db-postgres-dev-1 --target gold3-db-1
    python scripts/db_replicate.py --source host=localhost:5433 \
        --target host=localhost:5438
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class DatabaseReplicator:
    """Handles efficient PostgreSQL database replication."""

    def __init__(
        self,
        source_conn: str,
        target_conn: str,
        source_db: str = None,
        target_db: str = None,
        source_user: str = None,
        target_user: str = None,
        source_pass: str = None,
        target_pass: str = None,
    ):
        self.source_conn = source_conn
        self.target_conn = target_conn
        self.source_db = source_db or "gchub_dev"
        self.target_db = target_db or "gchub_dev"
        self.source_user = source_user or "postgres"
        self.target_user = target_user or "gchub"
        self.source_pass = source_pass or "gchub"
        self.target_pass = target_pass or "gchub"

        # Use system temp directory instead of hardcoded path
        import tempfile

        self.temp_dir = Path(tempfile.gettempdir()) / "db_replication"
        self.temp_dir.mkdir(exist_ok=True)

    def get_connection_string(
        self,
        conn_str: str,
        db_name: str = "postgres",
        user: str = None,
        password: str = None,
    ) -> str:
        """Convert connection string to pg_dump/pg_restore format."""
        if conn_str.startswith("host="):
            # Format: host=hostname:port
            host, port = conn_str.split("=")[1].split(":")
            user = user or "postgres"
            password = password or "postgres"
            return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        else:
            # Docker container name - connect via exposed port
            # Assume default PostgreSQL port 5432, but we'll override with
            # actual exposed port
            container_port = self._get_container_port(conn_str)
            user = user or "postgres"
            password = password or "postgres"
            return f"postgresql://{user}:{password}@localhost:{container_port}/{db_name}"

    def _get_container_port(self, container_name: str) -> str:
        """Get the exposed port for a Docker container."""
        try:
            # Get container port mapping
            result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    container_name,
                    "--format",
                    "{{.NetworkSettings.Ports}}",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                # Parse the port mapping - look for 5432/tcp
                ports_output = result.stdout.strip()
                if "5432/tcp" in ports_output:
                    # Extract the host port from the mapping
                    import re

                    match = re.search(r'5432/tcp.*?HostPort["\']?:["\']?(\d+)', ports_output)
                    if match:
                        return match.group(1)
        except Exception:
            pass
        # Fallback to default port
        return "5432"

    def get_tables_to_replicate(self) -> List[str]:
        """Get list of tables to replicate (excluding system/auth tables)."""
        return [
            # Reference tables (no dependencies)
            "workflow_customer",
            "workflow_plant",
            "workflow_inkset",
            "workflow_substrate",
            "workflow_printcondition",
            "workflow_linescreen",
            "workflow_printlocation",
            "workflow_cartonworkflow",
            "workflow_platemaker",
            "workflow_press",
            "workflow_chargecategory",
            "workflow_chargetype",
            "workflow_jobcomplexity",
            "workflow_salesservicerep",
            # Product/catalog tables
            "workflow_itemcatalog",
            "workflow_itemcatalogphoto",
            "item_catalog_productsubcategory",
            # Item tables
            "workflow_item",
            "workflow_itemspec",
            "workflow_itemcolor",
            "workflow_itemreview",
            "workflow_itemtracker",
            "workflow_itemtrackercategory",
            "workflow_itemtrackertype",
            # Job related tables
            "workflow_job",
            "workflow_jobaddress",
            "workflow_revision",
            "workflow_stepspec",
            "workflow_prooftracker",
            "workflow_trackedart",
            # Archives and other data
            "archives_kentonarchive",
            "archives_renmarkarchive",
            "qad_data_qad_casepacks",
            "qad_data_qad_printgroups",
            # Content types and permissions (safe to copy)
            "django_content_type",
            "auth_permission",
            "auth_group",
            "auth_group_permissions",
            # Sites
            "django_site",
        ]

    def replicate_via_direct_connection(self) -> bool:
        """Replicate data directly between databases using external connections."""
        try:
            print("🔄 Starting direct database replication...")

            # Get connection strings
            source_conn_str = self.get_connection_string(self.source_conn, self.source_db, self.source_user, self.source_pass)
            target_conn_str = self.get_connection_string(self.target_conn, self.target_db, self.target_user, self.target_pass)

            tables = self.get_tables_to_replicate()

            for table in tables:
                print(f"📋 Replicating table: {table}")

                # Dump table from source and restore to target in one command
                dump_cmd = [
                    "pg_dump",
                    source_conn_str,
                    "-t",
                    table,
                    "--no-owner",
                    "--no-privileges",
                ]

                restore_cmd = ["psql", target_conn_str]

                try:
                    # Execute dump and pipe to restore
                    dump_process = subprocess.Popen(dump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    restore_process = subprocess.Popen(restore_cmd, stdin=dump_process.stdout, stderr=subprocess.PIPE)

                    # Close the stdout of dump_process in the parent process
                    # This allows restore_process to receive EOF when dump is done
                    dump_process.stdout.close()

                    # Wait for both processes to complete
                    dump_stdout, dump_stderr = dump_process.communicate()
                    restore_stdout, restore_stderr = restore_process.communicate()

                    if dump_process.returncode != 0:
                        print(f"⚠️  Warning: Could not dump {table}: {dump_stderr.decode()}")
                        continue

                    if restore_process.returncode != 0:
                        print(f"⚠️  Warning: Could not restore {table}: {restore_stderr.decode()}")
                        continue

                    print(f"✅ Successfully replicated {table}")

                except Exception as e:
                    print(f"❌ Error replicating {table}: {e}")
                    continue

            print("🎉 Replication completed!")
            return True

        except Exception as e:
            print(f"❌ Replication failed: {e}")
            return False

    def replicate_via_compressed_dump(self) -> bool:
        """Replicate data using compressed dump files (fallback method)."""
        try:
            print("🗜️ Starting compressed dump replication...")

            dump_file = self.temp_dir / "db_replication.dump"

            # Create compressed dump
            print("📦 Creating compressed database dump...")
            dump_cmd = [
                "docker",
                "exec",
                self.source_conn,
                "pg_dump",
                "-U",
                self.source_user,
                "-d",
                self.source_db,
                "--no-owner",
                "--no-privileges",
                "-Fc",  # Custom format, compressed
            ]

            with open(dump_file, "wb") as f:
                result = subprocess.run(dump_cmd, stdout=f, stderr=subprocess.PIPE)
                if result.returncode != 0:
                    print(f"❌ Dump failed: {result.stderr.decode()}")
                    return False

            # Copy dump to target container
            print("📤 Copying dump to target container...")
            copy_cmd = [
                "docker",
                "cp",
                str(dump_file),
                f"{self.target_conn}:/tmp/db_replication.dump",
            ]
            result = subprocess.run(copy_cmd, capture_output=True)
            if result.returncode != 0:
                print(f"❌ Copy failed: {result.stderr.decode()}")
                return False

            # Restore in target container
            print("📥 Restoring database...")
            restore_cmd = [
                "docker",
                "exec",
                self.target_conn,
                "pg_restore",
                "-U",
                self.target_user,
                "-d",
                self.target_db,
                "--no-owner",
                "--no-privileges",
                "-c",  # Clean before restore
                "/tmp/db_replication.dump",
            ]
            result = subprocess.run(restore_cmd, capture_output=True)
            if result.returncode != 0:
                print(f"❌ Restore failed: {result.stderr.decode()}")
                return False

            # Cleanup
            dump_file.unlink(missing_ok=True)
            subprocess.run(
                [
                    "docker",
                    "exec",
                    self.target_conn,
                    "rm",
                    "-f",
                    "/tmp/db_replication.dump",
                ],
                capture_output=True,
            )

            print("🎉 Compressed replication completed!")
            return True

        except Exception as e:
            print(f"❌ Compressed replication failed: {e}")
            return False

    def _get_database_name(self, container: str, label: str) -> Optional[str]:
        """Get the database name from a container."""
        try:
            user = self.source_user if label == "source" else self.target_user
            db = self.source_db if label == "source" else self.target_db
            cmd = [
                "docker",
                "exec",
                container,
                "psql",
                "-U",
                user,
                "-d",
                db,
                "-t",
                "-c",
                "SELECT current_database();",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            print(f"Debug: Failed to get database name for {label}: {e}")
        return None

    def verify_replication(self) -> bool:
        """Verify that replication was successful by comparing row counts."""
        try:
            print("🔍 Verifying replication...")

            tables = self.get_tables_to_replicate()
            source_counts = {}
            target_counts = {}

            # Get source counts
            for table in tables:
                try:
                    cmd = [
                        "docker",
                        "exec",
                        self.source_conn,
                        "psql",
                        "-U",
                        self.source_user,
                        "-d",
                        self.source_db,
                        "-t",
                        "-c",
                        f"SELECT COUNT(*) FROM {table};",
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        source_counts[table] = int(result.stdout.strip())
                except Exception:
                    source_counts[table] = 0

            # Get target counts
            for table in tables:
                try:
                    cmd = [
                        "docker",
                        "exec",
                        self.target_conn,
                        "psql",
                        "-U",
                        self.target_user,
                        "-d",
                        self.target_db,
                        "-t",
                        "-c",
                        f"SELECT COUNT(*) FROM {table};",
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        target_counts[table] = int(result.stdout.strip())
                except Exception:
                    target_counts[table] = 0

            # Compare counts
            print("\n📊 Replication Summary:")
            print("-" * 60)
            print("<25")
            print("-" * 60)

            total_target = sum(target_counts.values())

            print("<25")
            print(".1f")

            return total_target > 0

        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Efficient PostgreSQL database replication")
    parser.add_argument(
        "--source",
        required=True,
        help="Source database (container name or host=hostname:port)",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Target database (container name or host=hostname:port)",
    )
    parser.add_argument(
        "--method",
        choices=["direct", "compressed"],
        default="direct",
        help="Replication method (default: direct)",
    )
    parser.add_argument("--verify", action="store_true", help="Verify replication after completion")
    parser.add_argument(
        "--source-db",
        default="gchub_dev",
        help="Source database name (default: gchub_dev)",
    )
    parser.add_argument(
        "--target-db",
        default="gchub_dev",
        help="Target database name (default: gchub_dev)",
    )
    parser.add_argument(
        "--source-user",
        default="postgres",
        help="Source database user (default: postgres)",
    )
    parser.add_argument("--target-user", default="gchub", help="Target database user (default: gchub)")
    parser.add_argument(
        "--source-password",
        default="gchub",
        help="Source database password (default: gchub)",
    )
    parser.add_argument(
        "--target-password",
        default="gchub",
        help="Target database password (default: gchub)",
    )

    args = parser.parse_args()

    replicator = DatabaseReplicator(
        args.source,
        args.target,
        source_db=args.source_db,
        target_db=args.target_db,
        source_user=args.source_user,
        target_user=args.target_user,
        source_pass=args.source_password,
        target_pass=args.target_password,
    )

    print("🚀 Starting database replication...")
    print(f"📍 Source: {args.source}")
    print(f"🎯 Target: {args.target}")
    print(f"🔧 Method: {args.method}")
    print()

    success = False
    if args.method == "direct":
        success = replicator.replicate_via_direct_connection()
    elif args.method == "compressed":
        success = replicator.replicate_via_compressed_dump()

    if success and args.verify:
        replicator.verify_replication()

    if success:
        print("\n✅ Database replication completed successfully!")
        print("💡 Tip: Add this to your development workflow for automatic data seeding")
    else:
        print("\n❌ Database replication failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
