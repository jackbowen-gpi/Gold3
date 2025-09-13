#!/usr/bin/env python3
"""
Gold3 Database - Comprehensive Field Masking Runner
Executes the comprehensive field masking script
"""

import subprocess
import sys
import os
from datetime import datetime


def run_masking_script():
    """Run the comprehensive field masking script"""

    script_path = "comprehensive_field_masking.sql"

    if not os.path.exists(script_path):
        print(f"❌ Error: {script_path} not found!")
        return False

    print("🔒 Gold3 Database - Comprehensive Field Masking")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Docker command to run the SQL script
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
        "gchub_db-postgres-dev-1:/tmp/comprehensive_field_masking.sql",
    ]

    try:
        print("📤 Copying SQL script to container...")
        result = subprocess.run(copy_cmd, capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode != 0:
            print(f"❌ Error copying file: {result.stderr}")
            return False

        print("✅ SQL script copied successfully")
        print()

        print("🚀 Executing masking operations...")
        print("⚠️  WARNING: This will modify your database data!")
        print()

        # Ask for confirmation
        response = input("Do you want to proceed with masking? (yes/no): ").lower().strip()

        if response not in ["yes", "y"]:
            print("❌ Masking operation cancelled by user")
            return False

        # Execute the masking
        result = subprocess.run(docker_cmd, capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            print("✅ Masking operations completed successfully!")
            print()
            print("📊 Results:")
            print(result.stdout)
        else:
            print(f"❌ Error during masking: {result.stderr}")
            return False

    except FileNotFoundError:
        print("❌ Error: Docker command not found. Make sure Docker is running.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    print()
    print(f"🏁 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return True


def show_masking_plan():
    """Show the masking plan without executing"""

    script_path = "comprehensive_field_masking.sql"

    if not os.path.exists(script_path):
        print(f"❌ Error: {script_path} not found!")
        return

    print("🔍 Gold3 Database - Masking Plan Preview")
    print("=" * 50)

    # Docker command to show the plan (without executing masking)
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
        -- Find all tables with target fields
        SELECT
            t.table_name,
            c.column_name,
            c.data_type,
            CASE
                WHEN c.column_name IN (\'phone_number\', \'phone\') THEN \'mask_phone\'
                WHEN c.column_name IN (\'email\', \'contact_email\', \'ship_to_email\') THEN \'mask_email\'
                WHEN c.column_name IN (\'first_name\', \'last_name\', \'contact_name\', \'name\') THEN \'mask_person_name\'
                WHEN c.column_name IN (\'address1\', \'address2\') THEN \'mask_address\'
                WHEN c.column_name = \'ip_address\' THEN \'mask_ip_address\'
                ELSE \'unknown\'
            END as masking_function,
            CASE WHEN t.table_name IN (SELECT tablename FROM pg_tables WHERE schemaname = \'public\')
                 THEN (SELECT n_tup_ins FROM pg_stat_user_tables WHERE relname = t.table_name)::INTEGER
                 ELSE 0
            END as estimated_rows
        FROM information_schema.tables t
        JOIN information_schema.columns c ON t.table_name = c.table_name
        WHERE t.table_schema = \'public\'
        AND t.table_type = \'BASE TABLE\'
        AND c.column_name IN (\'phone_number\', \'phone\', \'email\', \'contact_email\', \'ship_to_email\',
                             \'first_name\', \'last_name\', \'contact_name\', \'name\', \'address1\', \'address2\', \'ip_address\')
        AND t.table_name NOT IN (\'django_migrations\', \'django_content_type\', \'auth_permission\')
        ORDER BY estimated_rows DESC, t.table_name, c.column_name;
        """,
    ]

    try:
        result = subprocess.run(docker_cmd, capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            print("📋 Masking Plan:")
            print(result.stdout)
        else:
            print(f"❌ Error getting masking plan: {result.stderr}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--plan":
        show_masking_plan()
    else:
        print("🔒 Gold3 Database Field Masking Tool")
        print("=" * 40)
        print("This tool will mask sensitive fields across your database:")
        print("• Phone numbers (phone_number, phone)")
        print("• Email addresses (email, contact_email, ship_to_email)")
        print("• Names (first_name, last_name, contact_name, name)")
        print("• Addresses (address1, address2)")
        print("• IP addresses (ip_address)")
        print()
        print("⚠️  IMPORTANT: This will permanently modify your data!")
        print("   Make sure you have a backup before proceeding.")
        print()
        print("Usage:")
        print("  python comprehensive_field_masking.py --plan    # Show masking plan")
        print("  python comprehensive_field_masking.py           # Execute masking")
        print()

        run_masking_script()
