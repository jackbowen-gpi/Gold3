# Simplified script to merge users and groups using direct SQL
Write-Host "Merging production users and groups (simplified approach)..." -ForegroundColor Green

# Step 1: Copy groups from production, avoiding duplicates
Write-Host "Step 1: Merging groups..." -ForegroundColor Cyan
docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "
INSERT INTO auth_group (name)
SELECT DISTINCT name
FROM (VALUES
    ('ClemsonPersonnel'),
    ('EmailClarksvilleScheduling'),
    ('EmailPittstonScheduling'),
    ('MarionCartonScheduling'),
    ('SchedulingNotification'),
    ('BeveragePersonnel'),
    ('FoodservicePersonnel'),
    ('ContainerPersonnel'),
    ('CartonPersonnel'),
    ('GraphicSpecialists'),
    ('SalesPersonnel'),
    ('CSRPersonnel'),
    ('AdminPersonnel'),
    ('PlateOrderPersonnel')
) AS prod_groups(name)
WHERE name NOT IN (SELECT name FROM auth_group);
"

# Step 2: Get essential groups from production and recreate them
Write-Host "Step 2: Recreating essential production groups..." -ForegroundColor Cyan

# Get the actual group names from production
$prodGroups = docker exec postgres-backup-temp psql -U thundercuddles -d thundercuddles -c "SELECT name FROM auth_group;" | Where-Object { $_ -match "^\s\w+" } | ForEach-Object { $_.Trim() }

Write-Host "Found production groups, creating in dev..." -ForegroundColor Yellow

foreach ($group in $prodGroups) {
    if ($group -and $group.Length -gt 0 -and $group -ne "name" -and $group -notmatch "^\-+$" -and $group -notmatch "^\(\d+ row") {
        docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "INSERT INTO auth_group (name) VALUES ('$group') ON CONFLICT (name) DO NOTHING;" 2>$null
    }
}

# Step 3: Add a selection of production users (avoiding conflicts)
Write-Host "Step 3: Adding key production users..." -ForegroundColor Cyan

# Create some essential users with safe defaults
docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "
-- Add some test users if they don't exist
INSERT INTO auth_user (username, email, first_name, last_name, is_active, is_staff, is_superuser, password, date_joined)
SELECT 'test_artist', 'artist@test.com', 'Test', 'Artist', true, false, false, 'pbkdf2_sha256\$870000\$test\$test', NOW()
WHERE NOT EXISTS (SELECT 1 FROM auth_user WHERE username = 'test_artist');

INSERT INTO auth_user (username, email, first_name, last_name, is_active, is_staff, is_superuser, password, date_joined)
SELECT 'test_sales', 'sales@test.com', 'Test', 'Sales', true, false, false, 'pbkdf2_sha256\$870000\$test\$test', NOW()
WHERE NOT EXISTS (SELECT 1 FROM auth_user WHERE username = 'test_sales');

INSERT INTO auth_user (username, email, first_name, last_name, is_active, is_staff, is_superuser, password, date_joined)
SELECT 'test_csr', 'csr@test.com', 'Test', 'CSR', true, false, false, 'pbkdf2_sha256\$870000\$test\$test', NOW()
WHERE NOT EXISTS (SELECT 1 FROM auth_user WHERE username = 'test_csr');
"

# Step 4: Give dev_admin superuser status and add to key groups
Write-Host "Step 4: Configuring dev_admin permissions..." -ForegroundColor Cyan

docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "
-- Ensure dev_admin is superuser
UPDATE auth_user SET
    is_superuser = true,
    is_staff = true,
    is_active = true
WHERE username = 'dev_admin';

-- Add dev_admin to key groups
INSERT INTO auth_user_groups (user_id, group_id)
SELECT u.id, g.id
FROM auth_user u
CROSS JOIN auth_group g
WHERE u.username = 'dev_admin'
AND g.name IN ('ClemsonPersonnel', 'AdminPersonnel', 'BeveragePersonnel', 'FoodservicePersonnel', 'ContainerPersonnel', 'CartonPersonnel')
AND NOT EXISTS (
    SELECT 1 FROM auth_user_groups ug
    WHERE ug.user_id = u.id AND ug.group_id = g.id
);
"

# Step 5: Copy group permissions from production
Write-Host "Step 5: Copying group permissions..." -ForegroundColor Cyan

# Copy critical permissions directly
docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "
-- Ensure key permissions exist and are assigned to appropriate groups
-- This gives access to the main workflows

DO \$\$
DECLARE
    perm_id INTEGER;
    group_id INTEGER;
BEGIN
    -- Get permission IDs and assign to groups

    -- Foodservice access
    SELECT id INTO perm_id FROM auth_permission WHERE codename = 'foodservice_access';
    SELECT id INTO group_id FROM auth_group WHERE name = 'FoodservicePersonnel';
    IF perm_id IS NOT NULL AND group_id IS NOT NULL THEN
        INSERT INTO auth_group_permissions (group_id, permission_id) VALUES (group_id, perm_id) ON CONFLICT DO NOTHING;
    END IF;

    -- Beverage access
    SELECT id INTO perm_id FROM auth_permission WHERE codename = 'beverage_access';
    SELECT id INTO group_id FROM auth_group WHERE name = 'BeveragePersonnel';
    IF perm_id IS NOT NULL AND group_id IS NOT NULL THEN
        INSERT INTO auth_group_permissions (group_id, permission_id) VALUES (group_id, perm_id) ON CONFLICT DO NOTHING;
    END IF;

    -- Container access
    SELECT id INTO perm_id FROM auth_permission WHERE codename = 'container_access';
    SELECT id INTO group_id FROM auth_group WHERE name = 'ContainerPersonnel';
    IF perm_id IS NOT NULL AND group_id IS NOT NULL THEN
        INSERT INTO auth_group_permissions (group_id, permission_id) VALUES (group_id, perm_id) ON CONFLICT DO NOTHING;
    END IF;

    -- Carton access
    SELECT id INTO perm_id FROM auth_permission WHERE codename = 'carton_access';
    SELECT id INTO group_id FROM auth_group WHERE name = 'CartonPersonnel';
    IF perm_id IS NOT NULL AND group_id IS NOT NULL THEN
        INSERT INTO auth_group_permissions (group_id, permission_id) VALUES (group_id, perm_id) ON CONFLICT DO NOTHING;
    END IF;

END \$\$;
"

Write-Host "`n✅ Simplified user/group merge completed!" -ForegroundColor Green

# Show final counts
$userCount = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "SELECT COUNT(*) FROM auth_user;" | Select-String "\d+" | ForEach-Object { $_.Matches[0].Value }
$groupCount = docker exec gchub_db-postgres-dev-1 psql -U gchub -d gchub_dev -c "SELECT COUNT(*) FROM auth_group;" | Select-String "\d+" | ForEach-Object { $_.Matches[0].Value }

Write-Host "Final counts:" -ForegroundColor Green
Write-Host "  Users: $userCount" -ForegroundColor White
Write-Host "  Groups: $groupCount" -ForegroundColor White

Write-Host "`ndev_admin should now have access to the job search functionality!" -ForegroundColor Cyan
