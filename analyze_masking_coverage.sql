-- Analyze database schema and masking coverage
-- This script generates a comprehensive report of all tables, columns, and masking status

-- Get all tables and their columns
CREATE OR REPLACE FUNCTION analyze_masking_coverage()
RETURNS TABLE(
    table_name TEXT,
    column_name TEXT,
    data_type TEXT,
    is_nullable TEXT,
    masking_status TEXT,
    masking_details TEXT
) AS $$
DECLARE
    table_record RECORD;
    column_record RECORD;
    masking_found BOOLEAN := FALSE;
    masking_info TEXT := '';
BEGIN
    -- Loop through all tables
    FOR table_record IN
        SELECT t.tablename::TEXT as tablename
        FROM pg_tables t
        WHERE t.schemaname = 'public'
        ORDER BY t.tablename
    LOOP
        -- Loop through all columns in this table
        FOR column_record IN
            SELECT
                c.column_name::TEXT as column_name,
                c.data_type::TEXT as data_type,
                c.is_nullable::TEXT as is_nullable,
                c.column_default
            FROM information_schema.columns c
            WHERE c.table_schema = 'public'
            AND c.table_name = table_record.tablename
            ORDER BY c.ordinal_position
        LOOP
            -- Reset masking status for each column
            masking_found := FALSE;
            masking_info := 'Not masked - Review for sensitivity';

            -- Check for specific masking patterns in our masking script
            CASE
                WHEN table_record.tablename = 'auth_user' AND column_record.column_name IN ('username', 'first_name', 'last_name', 'email') THEN
                    masking_found := TRUE;
                    masking_info := 'Masked - User info anonymized';
                WHEN table_record.tablename = 'workflow_job' AND column_record.column_name IN ('name', 'brand_name', 'customer_name', 'customer_email', 'customer_phone', 'comments', 'instructions', 'po_number', 'customer_po_number', 'user_keywords', 'generated_keywords') THEN
                    masking_found := TRUE;
                    masking_info := 'Masked - Job/customer data anonymized';
                WHEN table_record.tablename = 'workflow_jobaddress' AND column_record.column_name IN ('name', 'company', 'address1', 'address2', 'city', 'zip', 'phone', 'email', 'cell_phone') THEN
                    masking_found := TRUE;
                    masking_info := 'Masked - Address/contact data anonymized';
                WHEN table_record.tablename = 'workflow_item' AND column_record.column_name IN ('bev_item_name', 'bev_imported_item_name', 'description') THEN
                    masking_found := TRUE;
                    masking_info := 'Masked - Product descriptions anonymized';
                WHEN column_record.column_name LIKE '%password%' THEN
                    masking_found := TRUE;
                    masking_info := 'Masked - Password field';
                WHEN column_record.column_name LIKE '%email%' AND masking_found = FALSE THEN
                    masking_found := TRUE;
                    masking_info := 'Masked - Email anonymized';
                WHEN column_record.column_name LIKE '%phone%' AND masking_found = FALSE THEN
                    masking_found := TRUE;
                    masking_info := 'Masked - Phone anonymized';
                WHEN column_record.column_name IN ('first_name', 'last_name', 'full_name') AND masking_found = FALSE THEN
                    masking_found := TRUE;
                    masking_info := 'Masked - Name anonymized';
                WHEN column_record.column_name LIKE '%address%' AND masking_found = FALSE THEN
                    masking_found := TRUE;
                    masking_info := 'Masked - Address anonymized';
                WHEN column_record.column_name LIKE '%comment%' AND masking_found = FALSE THEN
                    masking_found := TRUE;
                    masking_info := 'Masked - Comments anonymized';
                ELSE
                    masking_found := FALSE;
                    masking_info := 'Not masked - Review for sensitivity';
            END CASE;

            -- Return the result
            RETURN QUERY SELECT
                table_record.tablename,
                column_record.column_name,
                column_record.data_type,
                column_record.is_nullable,
                CASE WHEN masking_found THEN 'MASKED'::TEXT ELSE 'NOT_MASKED'::TEXT END,
                masking_info::TEXT;
        END LOOP;
    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Run the analysis
SELECT * FROM analyze_masking_coverage()
ORDER BY table_name, column_name;
