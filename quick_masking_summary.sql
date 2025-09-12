-- Quick Masking Coverage Summary
-- Shows key statistics and high-priority items

SELECT
    '=== QUICK MASKING SUMMARY ===' as summary,
    COUNT(*) as total_tables,
    SUM(CASE WHEN table_name IN ('auth_user', 'workflow_job', 'workflow_jobaddress', 'workflow_item') THEN 1 ELSE 0 END) as tables_with_masking,
    ROUND(
        (SUM(CASE WHEN table_name IN ('auth_user', 'workflow_job', 'workflow_jobaddress', 'workflow_item') THEN 1 ELSE 0 END) * 100.0) / COUNT(*),
        1
    ) as table_coverage_percentage
FROM (
    SELECT DISTINCT table_name
    FROM information_schema.columns
    WHERE table_schema = 'public'
) as unique_tables;

-- High-priority unmaksed columns
SELECT
    'HIGH PRIORITY - UNMASKED SENSITIVE DATA' as priority_level,
    table_name,
    column_name,
    data_type,
    CASE
        WHEN column_name LIKE '%phone%' THEN 'Phone Number'
        WHEN column_name LIKE '%email%' THEN 'Email Address'
        WHEN column_name LIKE '%address%' THEN 'Physical Address'
        WHEN column_name LIKE '%name%' THEN 'Personal/Business Name'
        WHEN column_name LIKE '%ip%' THEN 'IP Address'
        ELSE 'Other Sensitive Data'
    END as data_category
FROM information_schema.columns
WHERE table_schema = 'public'
AND (
    column_name LIKE '%phone%'
    OR column_name LIKE '%email%'
    OR column_name LIKE '%address%'
    OR column_name LIKE '%name%'
    OR column_name LIKE '%ip%'
)
AND table_name NOT IN ('auth_user', 'workflow_job', 'workflow_jobaddress', 'workflow_item')
ORDER BY
    CASE
        WHEN column_name LIKE '%phone%' THEN 1
        WHEN column_name LIKE '%email%' THEN 2
        WHEN column_name LIKE '%address%' THEN 3
        WHEN column_name LIKE '%name%' THEN 4
        ELSE 5
    END,
    table_name,
    column_name
LIMIT 20;
