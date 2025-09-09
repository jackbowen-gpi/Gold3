# Script to merge production groups and users while preserving dev_admin
Write-Host "Merging production groups and users with dev setup..." -ForegroundColor Green

# First, let's get the current dev_admin user ID to preserve it
$devAdminInfo = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "SELECT id, username FROM auth_user WHERE username = 'dev_admin';" | Select-String "\d+\s+\|\s+dev_admin"

if ($devAdminInfo) {
    Write-Host "✓ Found dev_admin user - will preserve this account" -ForegroundColor Green
} else {
    Write-Host "⚠ dev_admin user not found - continuing anyway" -ForegroundColor Yellow
}

# Step 1: Merge Groups (groups are usually safe to merge completely)
Write-Host "`nStep 1: Merging Groups..." -ForegroundColor Cyan

# Export groups from production
docker exec postgres-backup-temp pg_dump -U thundercuddles -d thundercuddles -t auth_group --data-only --no-owner > prod_groups.sql

# Copy to dev container
docker cp prod_groups.sql gchub_db-postgres-dev-1:/tmp/prod_groups.sql

# Import groups (this will add any missing groups)
Write-Host "Importing production groups..." -ForegroundColor Yellow
docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "
-- Create a temporary table for production groups
CREATE TEMP TABLE temp_prod_groups AS SELECT * FROM auth_group WHERE false;

-- Load production groups into temp table
\copy temp_prod_groups FROM '/tmp/prod_groups.sql' WITH CSV DELIMITER E'\t' QUOTE E'\b';

-- Insert only groups that don't already exist
INSERT INTO auth_group (name)
SELECT name FROM temp_prod_groups 
WHERE name NOT IN (SELECT name FROM auth_group);
"

# Step 2: Merge Group Permissions
Write-Host "`nStep 2: Merging Group Permissions..." -ForegroundColor Cyan

# Export group permissions from production
docker exec postgres-backup-temp pg_dump -U thundercuddles -d thundercuddles -t auth_group_permissions --data-only --no-owner > prod_group_perms.sql

# Copy to dev container
docker cp prod_group_perms.sql gchub_db-postgres-dev-1:/tmp/prod_group_perms.sql

# Import group permissions
Write-Host "Importing production group permissions..." -ForegroundColor Yellow
docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -f /tmp/prod_group_perms.sql 2>$null

# Step 3: Carefully merge users (excluding dev_admin)
Write-Host "`nStep 3: Adding production users (preserving dev_admin)..." -ForegroundColor Cyan

Write-Host "Creating safe user import..." -ForegroundColor Yellow

# Export production users to a CSV-like format for safer import
docker exec postgres-backup-temp psql -U thundercuddles -d thundercuddles -c "
\copy (SELECT id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined FROM auth_user WHERE username != 'dev_admin') TO '/tmp/prod_users.csv' WITH CSV HEADER;
"

# Copy the user data
docker cp postgres-backup-temp:/tmp/prod_users.csv ./prod_users.csv
docker cp prod_users.csv gchub_db-postgres-dev-1:/tmp/prod_users.csv

# Import users safely
docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "
-- Create temp table for production users
CREATE TEMP TABLE temp_prod_users AS SELECT * FROM auth_user WHERE false;

-- Load production users
\copy temp_prod_users FROM '/tmp/prod_users.csv' WITH CSV HEADER;

-- Insert users that don't conflict with existing usernames
INSERT INTO auth_user (password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined)
SELECT password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined 
FROM temp_prod_users 
WHERE username NOT IN (SELECT username FROM auth_user)
AND username != 'dev_admin';
"

# Step 4: Merge User-Group relationships
Write-Host "`nStep 4: Merging User-Group relationships..." -ForegroundColor Cyan

# Export user-group relationships
docker exec postgres-backup-temp pg_dump -U thundercuddles -d thundercuddles -t auth_user_groups --data-only --no-owner > prod_user_groups.sql

# Copy to dev
docker cp prod_user_groups.sql gchub_db-postgres-dev-1:/tmp/prod_user_groups.sql

# Import user-group relationships (with conflict handling)
docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "
-- Import user-group relationships, handling conflicts
CREATE TEMP TABLE temp_user_groups AS SELECT * FROM auth_user_groups WHERE false;

-- Load production data
\copy temp_user_groups FROM '/tmp/prod_user_groups.sql' WITH CSV DELIMITER E'\t' QUOTE E'\b';

-- Insert relationships for users and groups that exist, avoiding duplicates
INSERT INTO auth_user_groups (user_id, group_id)
SELECT DISTINCT ug.user_id, ug.group_id
FROM temp_user_groups ug
JOIN auth_user u ON u.id = ug.user_id
JOIN auth_group g ON g.id = ug.group_id
WHERE NOT EXISTS (
    SELECT 1 FROM auth_user_groups existing 
    WHERE existing.user_id = ug.user_id AND existing.group_id = ug.group_id
);
" 2>$null

# Step 5: Give dev_admin all permissions
Write-Host "`nStep 5: Ensuring dev_admin has all permissions..." -ForegroundColor Cyan

docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "
-- Make dev_admin a superuser with all permissions
UPDATE auth_user SET 
    is_superuser = true, 
    is_staff = true, 
    is_active = true 
WHERE username = 'dev_admin';

-- Add dev_admin to all groups (if not already there)
INSERT INTO auth_user_groups (user_id, group_id)
SELECT u.id, g.id
FROM auth_user u, auth_group g
WHERE u.username = 'dev_admin'
AND NOT EXISTS (
    SELECT 1 FROM auth_user_groups ug 
    WHERE ug.user_id = u.id AND ug.group_id = g.id
);
"

# Cleanup temp files
Remove-Item -Path "prod_groups.sql", "prod_group_perms.sql", "prod_user_groups.sql", "prod_users.csv" -ErrorAction SilentlyContinue

Write-Host "`n✅ User and Group merge completed!" -ForegroundColor Green
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  - Merged production groups with dev groups" -ForegroundColor White
Write-Host "  - Merged production users (preserved dev_admin)" -ForegroundColor White
Write-Host "  - Merged group permissions" -ForegroundColor White
Write-Host "  - Merged user-group relationships" -ForegroundColor White
Write-Host "  - Ensured dev_admin has all permissions" -ForegroundColor White

# Show final user count
$userCount = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "SELECT COUNT(*) FROM auth_user;" | Select-String "\d+" | ForEach-Object { $_.Matches[0].Value }
$groupCount = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "SELECT COUNT(*) FROM auth_group;" | Select-String "\d+" | ForEach-Object { $_.Matches[0].Value }

Write-Host "`nFinal counts:" -ForegroundColor Green
Write-Host "  Users: $userCount" -ForegroundColor White
Write-Host "  Groups: $groupCount" -ForegroundColor White
