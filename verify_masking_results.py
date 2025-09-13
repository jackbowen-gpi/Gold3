#!/usr/bin/env python3
"""
Gold3 Database - Masking Verification Runner
Verifies the results of field masking operations
"""

import subprocess
import sys
import os
from datetime import datetime


def run_verification():
    """Run the masking verification script"""

    script_path = "verify_masking_results.sql"

    if not os.path.exists(script_path):
        print(f"❌ Error: {script_path} not found!")
        return False

    print("🔍 Gold3 Database - Masking Verification")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Docker command to run the verification SQL script
    docker_cmd = [
        "docker",
        "exec",
        "gchub_db-postgres-dev-1",
        "psql",
        "-U",
        "postgres",
        "-d",
        "gchub_dev",
        "-f",
        f"/tmp/{script_path}",
    ]

    # Copy the SQL file to the container first
    copy_cmd = [
        "docker",
        "cp",
        script_path,
        "gchub_db-postgres-dev-1:/tmp/verify_masking_results.sql",
    ]

    try:
        print("📤 Copying verification script to container...")
        result = subprocess.run(copy_cmd, capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode != 0:
            print(f"❌ Error copying file: {result.stderr}")
            return False

        print("✅ Verification script copied successfully")
        print()

        print("🔍 Running verification checks...")
        result = subprocess.run(docker_cmd, capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            print("✅ Verification completed successfully!")
            print()
            print("📊 Verification Results:")
            print("=" * 30)
            print(result.stdout)
        else:
            print(f"❌ Error during verification: {result.stderr}")
            return False

    except FileNotFoundError:
        print("❌ Error: Docker command not found. Make sure Docker is running.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    print()
    print(f"🏁 Verification completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return True


def show_quick_status():
    """Show a quick status of masking without full verification"""

    print("📊 Gold3 Database - Quick Masking Status")
    print("=" * 50)

    # Quick query to show masking status
    docker_cmd = [
        "docker",
        "exec",
        "gchub_db-postgres-dev-1",
        "psql",
        "-U",
        "postgres",
        "-d",
        "gchub_dev",
        "-c",
        """
        SELECT
            COUNT(DISTINCT t.table_name) as tables_with_sensitive_fields,
            COUNT(*) as total_sensitive_fields,
            SUM(CASE WHEN t.table_name IN (SELECT tablename FROM pg_tables WHERE schemaname = \'public\')
                     THEN (SELECT n_tup_ins FROM pg_stat_user_tables WHERE relname = t.table_name)::INTEGER
                     ELSE 0 END) as estimated_total_rows
        FROM information_schema.tables t
        JOIN information_schema.columns c ON t.table_name = c.table_name
        WHERE t.table_schema = \'public\'
        AND t.table_type = \'BASE TABLE\'
        AND c.column_name IN (\'phone_number\', \'phone\', \'email\', \'contact_email\', \'ship_to_email\',
                             \'first_name\', \'last_name\', \'contact_name\', \'name\', \'address1\', \'address2\', \'ip_address\')
        AND t.table_name NOT IN (\'django_migrations\', \'django_content_type\', \'auth_permission\');
        """,
    ]

    try:
        result = subprocess.run(docker_cmd, capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            print("📋 Current Database Status:")
            print(result.stdout)
        else:
            print(f"❌ Error getting status: {result.stderr}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        show_quick_status()
    else:
        print("🔍 Gold3 Database Masking Verification Tool")
        print("=" * 45)
        print("This tool verifies that field masking was applied correctly.")
        print()
        print("Usage:")
        print("  python verify_masking_results.py --status    # Quick status check")
        print("  python verify_masking_results.py             # Full verification")
        print()

        run_verification()
