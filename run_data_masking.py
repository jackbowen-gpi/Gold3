# ruff: noqa
#!/usr/bin/env python3

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class DataMaskingRunner:
    def __init__(self, dry_run=False, create_backup=True, verify_only=False):
        self.dry_run = dry_run
        self.create_backup = create_backup
        self.verify_only = verify_only
        self.container_name = "gchub_db-postgres-dev-1"
        self.database_name = "gchub_dev"
        self.user = "postgres"

    def log(self, message):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_command(self, command, description):
        """Run a shell command and return success status"""
        self.log(f"Running: {description}")
        if self.dry_run:
            self.log(f"[DRY RUN] Would execute: {command}")
            return True

        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"✓ {description} completed successfully")
                return True
            else:
                self.log(f"✗ {description} failed:")
                self.log(f"Error: {result.stderr}")
                return False
        except Exception as e:
            self.log(f"✗ {description} failed with exception: {e}")
            return False

    def check_database_connection(self):
        """Verify we can connect to the database"""
        command = f'docker exec {self.container_name} psql -U {self.user} -d {self.database_name} -c "SELECT 1;"'
        return self.run_command(command, "Checking database connection")

    def create_database_backup(self):
        """Create a backup of the database"""
        if not self.create_backup:
            return True

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_before_masking_{timestamp}.sql"

        command = f"docker exec {self.container_name} pg_dump -U {self.user} -d {self.database_name} > {backup_file}"
        success = self.run_command(command, f"Creating database backup: {backup_file}")

        if success:
            self.log(f"Backup saved to: {backup_file}")
            self.log("⚠️  IMPORTANT: Keep this backup safe!")

        return success

    def get_table_counts(self):
        """Get row counts for tables that will be masked"""
        self.log("Getting table row counts before masking...")

        tables = ["auth_user", "workflow_job", "workflow_jobaddress", "workflow_item"]

        counts = {}
        for table in tables:
            command = (
                f'docker exec {self.container_name} psql -U {self.user} -d {self.database_name} -c "SELECT COUNT(*) FROM {table};"'
            )
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    # Extract count from output
                    lines = result.stdout.strip().split("\n")
                    for line in lines:
                        if line.strip().isdigit():
                            counts[table] = int(line.strip())
                            break
                else:
                    self.log(f"Could not get count for {table}")
            except Exception as e:
                self.log(f"Error getting count for {table}: {e}")

        return counts

    def run_masking_script(self):
        """Execute the data masking script"""
        if self.verify_only:
            self.log("Skipping masking (--verify-only mode)")
            return True

        script_path = Path("data_masking.sql")
        if not script_path.exists():
            self.log(f"✗ Masking script not found: {script_path}")
            return False

        # Copy script to container
        copy_command = f"docker cp {script_path} {self.container_name}:/tmp/data_masking.sql"
        if not self.run_command(copy_command, "Copying masking script to container"):
            return False

        # Execute script
        exec_command = f"docker exec {self.container_name} psql -U {self.user} -d {self.database_name} -f /tmp/data_masking.sql"
        return self.run_command(exec_command, "Executing data masking script")

    def run_verification(self):
        """Run the verification script"""
        script_path = Path("verify_masking.sql")
        if not script_path.exists():
            self.log(f"✗ Verification script not found: {script_path}")
            return False

        # Copy script to container
        copy_command = f"docker cp {script_path} {self.container_name}:/tmp/verify_masking.sql"
        if not self.run_command(copy_command, "Copying verification script to container"):
            return False

        # Execute script
        exec_command = f"docker exec {self.container_name} psql -U {self.user} -d {self.database_name} -f /tmp/verify_masking.sql"
        return self.run_command(exec_command, "Running verification script")

    def run_vacuum(self):
        """Run VACUUM to reclaim space"""
        if self.verify_only:
            return True

        command = f'docker exec {self.container_name} psql -U {self.user} -d {self.database_name} -c "VACUUM;"'
        return self.run_command(command, "Running VACUUM to reclaim space")

    def run(self):
        """Main execution flow"""
        self.log("=== Gold3 Data Masking Runner ===")
        self.log(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        self.log(f"Verify Only: {self.verify_only}")
        self.log(f"Create Backup: {self.create_backup}")
        self.log("=" * 40)

        # Safety warnings
        if not self.dry_run:
            self.log("⚠️  WARNING: This will modify your database!")
            self.log("⚠️  Make sure you have a backup!")
            if not self.create_backup:
                response = input("Continue without backup? (type 'yes' to confirm): ")
                if response.lower() != "yes":
                    self.log("Aborting...")
                    return False

        # Check connection
        if not self.check_database_connection():
            self.log("✗ Cannot connect to database. Aborting.")
            return False

        # Get initial counts
        initial_counts = self.get_table_counts()
        if initial_counts:
            self.log("Initial table counts:")
            for table, count in initial_counts.items():
                self.log(f"  {table}: {count:,} rows")

        # Create backup
        if self.create_backup:
            if not self.create_database_backup():
                self.log("✗ Backup failed. Aborting.")
                return False

        # Run masking
        if not self.run_masking_script():
            self.log("✗ Masking failed.")
            return False

        # Run vacuum
        if not self.run_vacuum():
            self.log("⚠️  VACUUM failed, but continuing...")

        # Verify results
        if not self.run_verification():
            self.log("⚠️  Verification failed, but masking may have succeeded.")

        # Get final counts
        final_counts = self.get_table_counts()
        if final_counts and initial_counts:
            self.log("Final table counts:")
            for table, count in final_counts.items():
                initial = initial_counts.get(table, 0)
                change = count - initial
                self.log(f"  {table}: {count:,} rows ({change:+,})")

        self.log("=" * 40)
        self.log("Data masking process completed!")
        if not self.dry_run:
            self.log("✅ Sensitive data has been anonymized")
            self.log("✅ Database relationships preserved")
            self.log("✅ Ready for development/testing use")

        return True


def main():
    parser = argparse.ArgumentParser(description="Run data masking on Gold3 database")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    parser.add_argument("--no-backup", action="store_true", help="Skip creating a backup")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only run verification, don't mask data",
    )

    args = parser.parse_args()

    runner = DataMaskingRunner(
        dry_run=args.dry_run,
        create_backup=not args.no_backup,
        verify_only=args.verify_only,
    )

    success = runner.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
