-- Gold3 Database - Masking Verification Script
-- Verifies that field masking was applied correctly

-- ===========================================
-- VERIFICATION QUERIES
-- ===========================================

-- Check masking function results
SELECT
    'Phone masking examples' as test_type,
    unnest(ARRAY[
        '(555) 123-4567',
        '555-123-4567',
        '15551234567',
        '+1 555 123 4567'
    ]) as original_value,
    unnest(ARRAY[
        mask_phone('(555) 123-4567'),
        mask_phone('555-123-4567'),
        mask_phone('15551234567'),
        mask_phone('+1 555 123 4567')
    ]) as masked_value
UNION ALL
SELECT
    'Email masking examples',
    unnest(ARRAY[
        'john.doe@example.com',
        'test.email@company.org',
        'a@b.co'
    ]),
    unnest(ARRAY[
        mask_email('john.doe@example.com'),
        mask_email('test.email@company.org'),
        mask_email('a@b.co')
    ])
UNION ALL
SELECT
    'Name masking examples',
    unnest(ARRAY[
        'John Doe',
        'Jane Smith',
        'A',
        'Bob'
    ]),
    unnest(ARRAY[
        mask_person_name('John Doe'),
        mask_person_name('Jane Smith'),
        mask_person_name('A'),
        mask_person_name('Bob')
    ])
UNION ALL
SELECT
    'Address masking examples',
    unnest(ARRAY[
        '123 Main Street',
        '456 Oak Avenue',
        '789 Pine Rd'
    ]),
    unnest(ARRAY[
        mask_address('123 Main Street'),
        mask_address('456 Oak Avenue'),
        mask_address('789 Pine Rd')
    ])
UNION ALL
SELECT
    'IP masking examples',
    unnest(ARRAY[
        '192.168.1.100',
        '10.0.0.1',
        '172.16.0.1'
    ]),
    unnest(ARRAY[
        mask_ip_address('192.168.1.100'),
        mask_ip_address('10.0.0.1'),
        mask_ip_address('172.16.0.1')
    ]);

-- ===========================================
-- CHECK MASKING STATUS BY TABLE
-- ===========================================

-- Create a comprehensive view of masking status
CREATE OR REPLACE VIEW masking_status AS
SELECT
    t.table_name,
    c.column_name,
    c.data_type,
    CASE
        WHEN c.column_name IN ('phone_number', 'phone') THEN 'Phone Number'
        WHEN c.column_name IN ('email', 'contact_email', 'ship_to_email') THEN 'Email Address'
        WHEN c.column_name IN ('first_name', 'last_name', 'contact_name') THEN 'Person Name'
        WHEN c.column_name = 'name' THEN 'Generic Name'
        WHEN c.column_name IN ('address1', 'address2') THEN 'Address'
        WHEN c.column_name = 'ip_address' THEN 'IP Address'
        ELSE 'Other'
    END as field_type,
    CASE
        WHEN c.column_name IN ('phone_number', 'phone') THEN 'mask_phone'
        WHEN c.column_name IN ('email', 'contact_email', 'ship_to_email') THEN 'mask_email'
        WHEN c.column_name IN ('first_name', 'last_name', 'contact_name', 'name') THEN 'mask_person_name'
        WHEN c.column_name IN ('address1', 'address2') THEN 'mask_address'
        WHEN c.column_name = 'ip_address' THEN 'mask_ip_address'
        ELSE 'unknown'
    END as masking_function,
    CASE WHEN t.table_name IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
         THEN (SELECT n_tup_ins FROM pg_stat_user_tables WHERE relname = t.table_name)::INTEGER
         ELSE 0
    END as estimated_rows,
    CASE
        WHEN c.column_name IN ('phone_number', 'phone') THEN
            (SELECT COUNT(*) FROM information_schema.columns c2
             WHERE c2.table_name = t.table_name AND c2.column_name = c.column_name
             AND c2.table_schema = 'public')
        ELSE 0
    END as has_phone_data,
    CASE
        WHEN c.column_name IN ('email', 'contact_email', 'ship_to_email') THEN
            (SELECT COUNT(*) FROM information_schema.columns c2
             WHERE c2.table_name = t.table_name AND c2.column_name = c.column_name
             AND c2.table_schema = 'public')
        ELSE 0
    END as has_email_data
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public'
AND t.table_type = 'BASE TABLE'
AND c.column_name IN ('phone_number', 'phone', 'email', 'contact_email', 'ship_to_email',
                     'first_name', 'last_name', 'contact_name', 'name', 'address1', 'address2', 'ip_address')
AND t.table_name NOT IN ('django_migrations', 'django_content_type', 'auth_permission')
ORDER BY t.table_name, c.column_name;

-- Show masking status summary
SELECT
    field_type,
    COUNT(*) as total_fields,
    COUNT(DISTINCT table_name) as tables_affected,
    SUM(estimated_rows) as total_estimated_rows
FROM masking_status
GROUP BY field_type
ORDER BY total_estimated_rows DESC;

-- Show detailed masking status by table
SELECT
    table_name,
    column_name,
    field_type,
    masking_function,
    estimated_rows,
    CASE
        WHEN estimated_rows > 10000 THEN '🔴 HIGH IMPACT'
        WHEN estimated_rows > 1000 THEN '🟡 MEDIUM IMPACT'
        ELSE '🟢 LOW IMPACT'
    END as impact_level
FROM masking_status
ORDER BY estimated_rows DESC, table_name, column_name;

-- ===========================================
-- SAMPLE DATA VERIFICATION
-- ===========================================

-- Check a few sample records from key tables to verify masking
DO $$
DECLARE
    table_record RECORD;
    sample_query TEXT;
    sample_result RECORD;
BEGIN
    RAISE NOTICE 'Checking sample masked data from key tables...';

    -- Check accounts_userprofile for phone and IP
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'accounts_userprofile') THEN
        RAISE NOTICE 'accounts_userprofile samples:';
        FOR sample_result IN
            SELECT phone_number, ip_address
            FROM accounts_userprofile
            WHERE phone_number IS NOT NULL OR ip_address IS NOT NULL
            LIMIT 3
        LOOP
            RAISE NOTICE '  Phone: %, IP: %', sample_result.phone_number, sample_result.ip_address;
        END LOOP;
    END IF;

    -- Check address_contact for various fields
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'address_contact') THEN
        RAISE NOTICE 'address_contact samples:';
        FOR sample_result IN
            SELECT first_name, last_name, email, phone, address1
            FROM address_contact
            WHERE first_name IS NOT NULL OR last_name IS NOT NULL OR email IS NOT NULL
            LIMIT 3
        LOOP
            RAISE NOTICE '  Name: % %, Email: %, Phone: %, Address: %',
                sample_result.first_name, sample_result.last_name,
                sample_result.email, sample_result.phone, sample_result.address1;
        END LOOP;
    END IF;

    -- Check workflow_job for customer data
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workflow_job') THEN
        RAISE NOTICE 'workflow_job samples:';
        FOR sample_result IN
            SELECT customer_name, customer_email, customer_phone
            FROM workflow_job
            WHERE customer_name IS NOT NULL OR customer_email IS NOT NULL
            LIMIT 3
        LOOP
            RAISE NOTICE '  Customer: %, Email: %, Phone: %',
                sample_result.customer_name, sample_result.customer_email, sample_result.customer_phone;
        END LOOP;
    END IF;

END $$;

-- ===========================================
-- COMPREHENSIVE MASKING REPORT
-- ===========================================

-- Generate final masking report
SELECT
    'Gold3 Database Masking Report' as report_title,
    CURRENT_DATE as report_date,
    CURRENT_TIME as report_time;

-- Summary statistics
SELECT
    COUNT(DISTINCT table_name) as tables_with_masked_fields,
    COUNT(*) as total_masked_fields,
    SUM(estimated_rows) as total_estimated_rows_affected
FROM masking_status;

-- Field type breakdown
SELECT
    field_type,
    COUNT(*) as field_count,
    ROUND(AVG(estimated_rows), 0) as avg_rows_per_table,
    MAX(estimated_rows) as max_rows_in_table
FROM masking_status
GROUP BY field_type
ORDER BY field_count DESC;

-- Tables with highest impact
SELECT
    table_name,
    COUNT(*) as fields_masked,
    SUM(estimated_rows) as total_rows,
    STRING_AGG(column_name, ', ') as masked_columns
FROM masking_status
GROUP BY table_name
ORDER BY total_rows DESC
LIMIT 10;

-- ===========================================
-- CLEANUP (Optional)
-- ===========================================

-- Uncomment these lines if you want to clean up temporary objects
-- DROP VIEW IF EXISTS masking_status;
-- DROP FUNCTION IF EXISTS execute_masking_operations();
-- DROP FUNCTION IF EXISTS mask_phone(TEXT);
-- DROP FUNCTION IF EXISTS mask_email(TEXT);
-- DROP FUNCTION IF EXISTS mask_person_name(TEXT);
-- DROP FUNCTION IF EXISTS mask_address(TEXT);
-- DROP FUNCTION IF EXISTS mask_ip_address(TEXT);
