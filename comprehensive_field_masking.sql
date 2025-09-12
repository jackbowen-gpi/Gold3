-- Gold3 Database - Comprehensive Field Masking Script
-- Masks sensitive fields across all tables in the database

-- ===========================================
-- STEP 1: CREATE MASKING FUNCTIONS
-- ===========================================

-- Function to mask phone numbers
CREATE OR REPLACE FUNCTION mask_phone(phone_text TEXT)
RETURNS TEXT AS $$
BEGIN
    IF phone_text IS NULL THEN
        RETURN NULL;
    END IF;

    -- Remove all non-digit characters for processing
    phone_text := regexp_replace(phone_text, '[^0-9]', '', 'g');

    -- If it's a 10-digit US phone number, format as (XXX) XXX-XXXX
    IF length(phone_text) = 10 THEN
        RETURN '(' || substring(phone_text, 1, 3) || ') ' ||
               substring(phone_text, 4, 3) || '-' ||
               substring(phone_text, 7, 4);
    -- If it's an 11-digit number (with country code), format accordingly
    ELSIF length(phone_text) = 11 AND substring(phone_text, 1, 1) = '1' THEN
        RETURN '+1 (' || substring(phone_text, 2, 3) || ') ' ||
               substring(phone_text, 5, 3) || '-' ||
               substring(phone_text, 8, 4);
    -- For other formats, mask the middle digits
    ELSE
        RETURN substring(phone_text, 1, 3) || 'XXX' || substring(phone_text, length(phone_text)-2, 3);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to mask email addresses
CREATE OR REPLACE FUNCTION mask_email(email_text TEXT)
RETURNS TEXT AS $$
DECLARE
    at_pos INTEGER;
    domain_part TEXT;
    local_part TEXT;
BEGIN
    IF email_text IS NULL OR email_text = '' THEN
        RETURN email_text;
    END IF;

    at_pos := position('@' in email_text);

    IF at_pos > 0 THEN
        local_part := substring(email_text, 1, at_pos - 1);
        domain_part := substring(email_text, at_pos);

        -- Keep first 2-3 characters of local part, mask the rest
        IF length(local_part) <= 3 THEN
            local_part := local_part;
        ELSE
            local_part := substring(local_part, 1, 2) || '***';
        END IF;

        RETURN local_part || domain_part;
    ELSE
        -- If no @ found, just mask the whole thing
        RETURN substring(email_text, 1, 3) || '***';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to mask person names
CREATE OR REPLACE FUNCTION mask_person_name(name_text TEXT)
RETURNS TEXT AS $$
BEGIN
    IF name_text IS NULL OR name_text = '' THEN
        RETURN name_text;
    END IF;

    -- For names, keep first letter and mask the rest
    IF length(name_text) <= 2 THEN
        RETURN name_text;
    ELSE
        RETURN substring(name_text, 1, 1) || repeat('*', length(name_text) - 1);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to mask addresses
CREATE OR REPLACE FUNCTION mask_address(address_text TEXT)
RETURNS TEXT AS $$
BEGIN
    IF address_text IS NULL OR address_text = '' THEN
        RETURN address_text;
    END IF;

    -- Keep first few characters and mask the rest
    IF length(address_text) <= 5 THEN
        RETURN address_text;
    ELSE
        RETURN substring(address_text, 1, 3) || repeat('*', length(address_text) - 3);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to mask IP addresses
CREATE OR REPLACE FUNCTION mask_ip_address(ip_text TEXT)
RETURNS TEXT AS $$
BEGIN
    IF ip_text IS NULL OR ip_text = '' THEN
        RETURN ip_text;
    END IF;

    -- For IPv4 addresses, mask the last two octets
    IF ip_text ~ '^\d+\.\d+\.\d+\.\d+$' THEN
        RETURN regexp_replace(ip_text, '^(\d+\.\d+)\.(\d+\.\d+)$', '\1.***.***');
    -- For other formats, mask most of the content
    ELSE
        RETURN substring(ip_text, 1, 3) || '***';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- STEP 2: FIND ALL TABLES WITH TARGET FIELDS
-- ===========================================

-- Create a temporary table to store the masking operations
CREATE TEMP TABLE masking_operations (
    table_name TEXT,
    column_name TEXT,
    data_type TEXT,
    masking_function TEXT,
    estimated_rows INTEGER
);

-- Find all tables with phone-related fields
INSERT INTO masking_operations
SELECT
    t.table_name,
    c.column_name,
    c.data_type,
    CASE
        WHEN c.column_name IN ('phone_number', 'phone') THEN 'mask_phone'
        ELSE 'mask_phone'
    END as masking_function,
    CASE WHEN t.table_name IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
         THEN (SELECT n_tup_ins FROM pg_stat_user_tables WHERE relname = t.table_name)::INTEGER
         ELSE 0
    END as estimated_rows
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public'
AND t.table_type = 'BASE TABLE'
AND c.column_name IN ('phone_number', 'phone')
ORDER BY t.table_name, c.column_name;

-- Find all tables with email-related fields
INSERT INTO masking_operations
SELECT
    t.table_name,
    c.column_name,
    c.data_type,
    'mask_email' as masking_function,
    CASE WHEN t.table_name IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
         THEN (SELECT n_tup_ins FROM pg_stat_user_tables WHERE relname = t.table_name)::INTEGER
         ELSE 0
    END as estimated_rows
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public'
AND t.table_type = 'BASE TABLE'
AND c.column_name IN ('email', 'contact_email', 'ship_to_email')
ORDER BY t.table_name, c.column_name;

-- Find all tables with name-related fields
INSERT INTO masking_operations
SELECT
    t.table_name,
    c.column_name,
    c.data_type,
    'mask_person_name' as masking_function,
    CASE WHEN t.table_name IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
         THEN (SELECT n_tup_ins FROM pg_stat_user_tables WHERE relname = t.table_name)::INTEGER
         ELSE 0
    END as estimated_rows
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public'
AND t.table_type = 'BASE TABLE'
AND c.column_name IN ('first_name', 'last_name', 'contact_name')
ORDER BY t.table_name, c.column_name;

-- Find all tables with address-related fields
INSERT INTO masking_operations
SELECT
    t.table_name,
    c.column_name,
    c.data_type,
    'mask_address' as masking_function,
    CASE WHEN t.table_name IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
         THEN (SELECT n_tup_ins FROM pg_stat_user_tables WHERE relname = t.table_name)::INTEGER
         ELSE 0
    END as estimated_rows
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public'
AND t.table_type = 'BASE TABLE'
AND c.column_name IN ('address1', 'address2')
ORDER BY t.table_name, c.column_name;

-- Find all tables with IP address fields
INSERT INTO masking_operations
SELECT
    t.table_name,
    c.column_name,
    c.data_type,
    'mask_ip_address' as masking_function,
    CASE WHEN t.table_name IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
         THEN (SELECT n_tup_ins FROM pg_stat_user_tables WHERE relname = t.table_name)::INTEGER
         ELSE 0
    END as estimated_rows
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public'
AND t.table_type = 'BASE TABLE'
AND c.column_name IN ('ip_address')
ORDER BY t.table_name, c.column_name;

-- Find tables with generic 'name' field (but exclude system tables and known non-sensitive tables)
INSERT INTO masking_operations
SELECT
    t.table_name,
    c.column_name,
    c.data_type,
    'mask_person_name' as masking_function,
    CASE WHEN t.table_name IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
         THEN (SELECT n_tup_ins FROM pg_stat_user_tables WHERE relname = t.table_name)::INTEGER
         ELSE 0
    END as estimated_rows
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public'
AND t.table_type = 'BASE TABLE'
AND c.column_name = 'name'
AND t.table_name NOT IN ('django_migrations', 'django_content_type', 'auth_permission')
ORDER BY t.table_name, c.column_name;

-- ===========================================
-- STEP 3: DISPLAY MASKING PLAN
-- ===========================================

-- Show the masking plan
SELECT
    table_name,
    column_name,
    data_type,
    masking_function,
    estimated_rows,
    CASE
        WHEN estimated_rows > 10000 THEN 'HIGH IMPACT'
        WHEN estimated_rows > 1000 THEN 'MEDIUM IMPACT'
        ELSE 'LOW IMPACT'
    END as impact_level
FROM masking_operations
ORDER BY estimated_rows DESC, table_name, column_name;

-- ===========================================
-- STEP 4: EXECUTE MASKING OPERATIONS
-- ===========================================

-- Create a function to execute masking operations dynamically
CREATE OR REPLACE FUNCTION execute_masking_operations()
RETURNS TABLE (
    table_name TEXT,
    column_name TEXT,
    rows_affected INTEGER,
    execution_time INTERVAL
) AS $$
DECLARE
    operation_record RECORD;
    sql_command TEXT;
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    affected_count INTEGER;
BEGIN
    -- Create temporary results table
    CREATE TEMP TABLE IF NOT EXISTS masking_results (
        table_name TEXT,
        column_name TEXT,
        rows_affected INTEGER,
        execution_time INTERVAL
    );

    -- Execute each masking operation
    FOR operation_record IN SELECT * FROM masking_operations ORDER BY estimated_rows ASC
    LOOP
        start_time := clock_timestamp();

        -- Build the UPDATE statement
        sql_command := format(
            'UPDATE %I SET %I = %s(%I) WHERE %I IS NOT NULL',
            operation_record.table_name,
            operation_record.column_name,
            operation_record.masking_function,
            operation_record.column_name,
            operation_record.column_name
        );

        -- Execute the command
        BEGIN
            EXECUTE sql_command;
            GET DIAGNOSTICS affected_count = ROW_COUNT;
            end_time := clock_timestamp();

            -- Insert result
            INSERT INTO masking_results VALUES (
                operation_record.table_name,
                operation_record.column_name,
                affected_count,
                end_time - start_time
            );

        EXCEPTION WHEN OTHERS THEN
            -- Log error but continue with other operations
            RAISE NOTICE 'Error masking %.%: %', operation_record.table_name, operation_record.column_name, SQLERRM;
            INSERT INTO masking_results VALUES (
                operation_record.table_name,
                operation_record.column_name,
                -1,  -- Error indicator
                INTERVAL '0 seconds'
            );
        END;
    END LOOP;

    -- Return results
    RETURN QUERY SELECT * FROM masking_results ORDER BY rows_affected DESC;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- STEP 5: EXECUTE THE MASKING (UNCOMMENT TO RUN)
-- ===========================================

-- WARNING: This will modify your data permanently!
-- Make sure you have a backup before running this!

/*
-- Execute the masking operations
SELECT * FROM execute_masking_operations();

-- Show summary of masking results
SELECT
    COUNT(*) as total_operations,
    SUM(rows_affected) as total_rows_affected,
    AVG(execution_time) as avg_execution_time
FROM masking_results
WHERE rows_affected >= 0;
*/

-- ===========================================
-- STEP 6: VERIFICATION QUERIES
-- ===========================================

-- Check if masking functions work correctly
SELECT
    'Phone masking test' as test_type,
    '(555) 123-4567' as original,
    mask_phone('(555) 123-4567') as masked
UNION ALL
SELECT
    'Email masking test',
    'john.doe@example.com',
    mask_email('john.doe@example.com')
UNION ALL
SELECT
    'Name masking test',
    'John Doe',
    mask_person_name('John Doe')
UNION ALL
SELECT
    'Address masking test',
    '123 Main Street',
    mask_address('123 Main Street')
UNION ALL
SELECT
    'IP masking test',
    '192.168.1.100',
    mask_ip_address('192.168.1.100');

-- Show current masking status after operations
SELECT
    mo.table_name,
    mo.column_name,
    mo.masking_function,
    COUNT(*) as rows_with_data
FROM masking_operations mo
JOIN information_schema.tables t ON mo.table_name = t.table_name
WHERE t.table_schema = 'public'
GROUP BY mo.table_name, mo.column_name, mo.masking_function
ORDER BY mo.table_name, mo.column_name;
