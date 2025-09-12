-- Data Masking Verification Script
-- Run this after executing the main masking script to verify results

-- Check auth_user masking
SELECT
    'auth_user' as table_name,
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE username LIKE 'user_%') as masked_usernames,
    COUNT(*) FILTER (WHERE email LIKE '%@example.com' OR email LIKE '%@testcompany.com') as masked_emails
FROM auth_user;

-- Check workflow_job masking
SELECT
    'workflow_job' as table_name,
    COUNT(*) as total_jobs,
    COUNT(*) FILTER (WHERE brand_name LIKE 'Global%' OR brand_name LIKE 'National%' OR brand_name LIKE 'International%') as masked_brands,
    COUNT(*) FILTER (WHERE customer_name LIKE 'Global%' OR customer_name LIKE 'National%') as masked_customers,
    COUNT(*) FILTER (WHERE customer_email LIKE '%@example.com' OR customer_email LIKE '%@testcompany.com') as masked_emails,
    COUNT(*) FILTER (WHERE vrml_password LIKE 'masked_password_%') as masked_passwords
FROM workflow_job;

-- Check workflow_jobaddress masking
SELECT
    'workflow_jobaddress' as table_name,
    COUNT(*) as total_addresses,
    COUNT(*) FILTER (WHERE company LIKE 'Global%' OR company LIKE 'National%') as masked_companies,
    COUNT(*) FILTER (WHERE name LIKE 'John%' OR name LIKE 'Jane%') as masked_names,
    COUNT(*) FILTER (WHERE address1 LIKE '1%' OR address1 LIKE '2%') as masked_addresses,
    COUNT(*) FILTER (WHERE email LIKE '%@example.com') as masked_emails
FROM workflow_jobaddress;

-- Sample of masked data (first 5 records)
SELECT 'Sample workflow_job records:' as info;
SELECT id, brand_name, customer_name, customer_email, customer_phone
FROM workflow_job
ORDER BY id
LIMIT 5;

SELECT 'Sample auth_user records:' as info;
SELECT id, username, first_name, last_name, email
FROM auth_user
ORDER BY id
LIMIT 5;

SELECT 'Sample workflow_jobaddress records:' as info;
SELECT id, name, company, address1, city, email
FROM workflow_jobaddress
ORDER BY id
LIMIT 5;
