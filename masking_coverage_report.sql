-- Comprehensive Data Masking Coverage Report
-- Generated on: September 12, 2025

-- This report shows all tables, columns, and their masking status

-- First, let's get a summary of masking coverage by table
SELECT
    '=== MASKING COVERAGE SUMMARY ===' as report_section,
    COUNT(*) as total_tables
FROM pg_tables
WHERE schemaname = 'public';

-- Get detailed column information for key tables
SELECT
    '=== AUTH_USER TABLE ===' as table_info,
    c.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    CASE
        WHEN c.column_name IN ('username', 'first_name', 'last_name', 'email') THEN 'MASKED - User info anonymized'
        WHEN c.column_name LIKE '%password%' THEN 'MASKED - Password field'
        ELSE 'NOT_MASKED - Review for sensitivity'
    END as masking_status
FROM information_schema.columns c
WHERE c.table_schema = 'public' AND c.table_name = 'auth_user'
ORDER BY c.ordinal_position;

SELECT
    '=== WORKFLOW_JOB TABLE ===' as table_info,
    c.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    CASE
        WHEN c.column_name IN ('name', 'brand_name', 'customer_name', 'customer_email', 'customer_phone', 'comments', 'instructions', 'po_number', 'customer_po_number', 'user_keywords', 'generated_keywords') THEN 'MASKED - Job/customer data anonymized'
        WHEN c.column_name LIKE '%password%' THEN 'MASKED - Password field'
        WHEN c.column_name LIKE '%email%' THEN 'MASKED - Email anonymized'
        WHEN c.column_name LIKE '%phone%' THEN 'MASKED - Phone anonymized'
        WHEN c.column_name LIKE '%comment%' THEN 'MASKED - Comments anonymized'
        ELSE 'NOT_MASKED - Review for sensitivity'
    END as masking_status
FROM information_schema.columns c
WHERE c.table_schema = 'public' AND c.table_name = 'workflow_job'
ORDER BY c.ordinal_position;

SELECT
    '=== WORKFLOW_JOBADDRESS TABLE ===' as table_info,
    c.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    CASE
        WHEN c.column_name IN ('name', 'company', 'address1', 'address2', 'city', 'zip', 'phone', 'email', 'cell_phone') THEN 'MASKED - Address/contact data anonymized'
        WHEN c.column_name LIKE '%email%' THEN 'MASKED - Email anonymized'
        WHEN c.column_name LIKE '%phone%' THEN 'MASKED - Phone anonymized'
        WHEN c.column_name LIKE '%address%' THEN 'MASKED - Address anonymized'
        ELSE 'NOT_MASKED - Review for sensitivity'
    END as masking_status
FROM information_schema.columns c
WHERE c.table_schema = 'public' AND c.table_name = 'workflow_jobaddress'
ORDER BY c.ordinal_position;

SELECT
    '=== WORKFLOW_ITEM TABLE ===' as table_info,
    c.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    CASE
        WHEN c.column_name IN ('bev_item_name', 'bev_imported_item_name', 'description') THEN 'MASKED - Product descriptions anonymized'
        WHEN c.column_name LIKE '%comment%' THEN 'MASKED - Comments anonymized'
        ELSE 'NOT_MASKED - Review for sensitivity'
    END as masking_status
FROM information_schema.columns c
WHERE c.table_schema = 'public' AND c.table_name = 'workflow_item'
ORDER BY c.ordinal_position;

-- Check for potentially sensitive columns across all tables
SELECT
    '=== POTENTIALLY SENSITIVE COLUMNS (NOT CURRENTLY MASKED) ===' as sensitive_check,
    c.table_name,
    c.column_name,
    c.data_type,
    'POTENTIAL SENSITIVE DATA - REVIEW' as status
FROM information_schema.columns c
WHERE c.table_schema = 'public'
AND (
    c.column_name LIKE '%email%'
    OR c.column_name LIKE '%phone%'
    OR c.column_name LIKE '%address%'
    OR c.column_name LIKE '%name%'
    OR c.column_name LIKE '%password%'
    OR c.column_name LIKE '%social%'
    OR c.column_name LIKE '%ssn%'
    OR c.column_name LIKE '%credit%'
    OR c.column_name LIKE '%card%'
    OR c.column_name LIKE '%comment%'
    OR c.column_name LIKE '%note%'
)
AND c.table_name NOT IN ('auth_user', 'workflow_job', 'workflow_jobaddress', 'workflow_item')
ORDER BY c.table_name, c.column_name;

-- Summary statistics
SELECT
    '=== MASKING COVERAGE STATISTICS ===' as stats_section,
    COUNT(*) as total_columns,
    SUM(CASE WHEN masking_status = 'MASKED' THEN 1 ELSE 0 END) as masked_columns,
    ROUND(
        (SUM(CASE WHEN masking_status = 'MASKED' THEN 1 ELSE 0 END) * 100.0) / COUNT(*),
        2
    ) as masking_percentage
FROM (
    SELECT
        c.table_name,
        c.column_name,
        CASE
            WHEN c.table_name = 'auth_user' AND c.column_name IN ('username', 'first_name', 'last_name', 'email') THEN 'MASKED'
            WHEN c.table_name = 'workflow_job' AND c.column_name IN ('name', 'brand_name', 'customer_name', 'customer_email', 'customer_phone', 'comments', 'instructions', 'po_number', 'customer_po_number', 'user_keywords', 'generated_keywords') THEN 'MASKED'
            WHEN c.table_name = 'workflow_jobaddress' AND c.column_name IN ('name', 'company', 'address1', 'address2', 'city', 'zip', 'phone', 'email', 'cell_phone') THEN 'MASKED'
            WHEN c.table_name = 'workflow_item' AND c.column_name IN ('bev_item_name', 'bev_imported_item_name', 'description') THEN 'MASKED'
            WHEN c.column_name LIKE '%password%' THEN 'MASKED'
            WHEN c.column_name LIKE '%email%' AND c.table_name NOT IN ('auth_user', 'workflow_job', 'workflow_jobaddress') THEN 'MASKED'
            WHEN c.column_name LIKE '%phone%' AND c.table_name NOT IN ('workflow_job', 'workflow_jobaddress') THEN 'MASKED'
            WHEN c.column_name LIKE '%address%' AND c.table_name NOT IN ('workflow_jobaddress') THEN 'MASKED'
            WHEN c.column_name LIKE '%comment%' AND c.table_name NOT IN ('workflow_job', 'workflow_item') THEN 'MASKED'
            ELSE 'NOT_MASKED'
        END as masking_status
    FROM information_schema.columns c
    WHERE c.table_schema = 'public'
) as coverage_stats;
