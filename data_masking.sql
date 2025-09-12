-- Data Masking Script for Gold3 Database
-- This script anonymizes sensitive data while preserving functionality
-- Run this on a COPY of your production database, NEVER on production!

-- =====================================================
-- PART 1: CREATE MASKING FUNCTIONS
-- =====================================================

-- Function to generate random company names (preserving dairy/farm patterns)
CREATE OR REPLACE FUNCTION mask_brand_name(original_brand TEXT)
RETURNS TEXT AS $$
DECLARE
    dairy_prefixes TEXT[] := ARRAY['Dairy', 'Farm', 'Cream', 'Milk', 'Cheese', 'Butter', 'Yogurt', 'Ice Cream'];
    dairy_suffixes TEXT[] := ARRAY['Farms', 'Dairy', 'Creamery', 'Products', 'Foods', 'Company', 'Cooperative', 'Corporation'];
    generic_prefixes TEXT[] := ARRAY['Global', 'National', 'Premier', 'United', 'American', 'Pacific', 'Atlantic', 'Continental'];
    generic_suffixes TEXT[] := ARRAY['Industries', 'Corporation', 'Enterprises', 'Solutions', 'Group', 'Partners', 'Systems', 'Services'];
    result TEXT;
BEGIN
    IF original_brand IS NULL OR original_brand = '' THEN
        RETURN original_brand;
    END IF;

    -- Check if original contains dairy/farm keywords
    IF original_brand ~* '(dairy|farm|cream|milk|cheese|butter|yogurt|ice|creamery)' THEN
        -- Preserve dairy/farm theme
        result := dairy_prefixes[1 + (random() * (array_length(dairy_prefixes, 1) - 1))::integer] || ' ' ||
                  dairy_suffixes[1 + (random() * (array_length(dairy_suffixes, 1) - 1))::integer];
    ELSE
        -- Generic company name
        result := generic_prefixes[1 + (random() * (array_length(generic_prefixes, 1) - 1))::integer] || ' ' ||
                  generic_suffixes[1 + (random() * (array_length(generic_suffixes, 1) - 1))::integer];
    END IF;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to generate random job names (preserving product/campaign patterns)
CREATE OR REPLACE FUNCTION mask_job_name(original_name TEXT)
RETURNS TEXT AS $$
DECLARE
    prefixes TEXT[] := ARRAY['Holiday', 'Summer', 'Winter', 'Spring', 'Fall', 'Christmas', 'Thanksgiving', 'Easter', 'Valentine', 'Halloween'];
    products TEXT[] := ARRAY['Cup', 'Carton', 'Bottle', 'Can', 'Pail', 'Box', 'Plate', 'Lid', 'Straw', 'Napkin'];
    campaigns TEXT[] := ARRAY['DMR', 'DFMS', 'LCRS', 'RTW', 'DMRL', 'LCRSSL', 'JCWS', 'PCF', 'PLA', 'KD'];
    suffixes TEXT[] := ARRAY['Graphics', 'Design', 'Remake', 'New', 'Update', 'Revision', 'Special', 'Limited', 'Premium', 'Deluxe'];
    result TEXT;
    year_pattern TEXT;
BEGIN
    IF original_name IS NULL OR original_name = '' THEN
        RETURN original_name;
    END IF;

    -- Check for year patterns (like "2023", "Holiday 2023")
    IF original_name ~ '\b(20\d{2})\b' THEN
        year_pattern := substring(original_name from '\b(20\d{2})\b');
    END IF;

    -- Check for product keywords and preserve them
    IF original_name ~* '\b(cup|carton|bottle|can|pail|box|plate|lid|straw|napkin)\b' THEN
        -- Extract the product word
        result := regexp_replace(original_name, '.*\b(cup|carton|bottle|can|pail|box|plate|lid|straw|napkin)\b.*', '\1', 'i');
        -- Add a random prefix
        result := prefixes[1 + (random() * (array_length(prefixes, 1) - 1))::integer] || ' ' || initcap(result);
    ELSIF original_name ~* '\b(DMR|DFMS|LCRS|RTW|DMRL|LCRSSL|JCWS|PCF|PLA|KD)\b' THEN
        -- Preserve campaign codes
        result := regexp_replace(original_name, '.*\b(DMR|DFMS|LCRS|RTW|DMRL|LCRSSL|JCWS|PCF|PLA|KD)\b.*', '\1', 'i');
        result := result || '-' || (20 + (random() * 10)::integer)::text;
    ELSE
        -- Generic job name
        result := prefixes[1 + (random() * (array_length(prefixes, 1) - 1))::integer] || ' ' ||
                  suffixes[1 + (random() * (array_length(suffixes, 1) - 1))::integer];
    END IF;

    -- Add year if original had one
    IF year_pattern IS NOT NULL THEN
        result := result || ' ' || year_pattern;
    END IF;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to generate random customer names (preserving business patterns)
CREATE OR REPLACE FUNCTION mask_customer_name(original_customer TEXT)
RETURNS TEXT AS $$
DECLARE
    business_types TEXT[] := ARRAY['Restaurant', 'Dairy', 'Farm', 'Foods', 'Bakery', 'Cafe', 'Market', 'Store', 'Group', 'Company'];
    locations TEXT[] := ARRAY['Athens', 'Kalamazoo', 'Shelbyville', 'Wausau', 'Baton Rouge', 'Ft Wayne', 'Somerset', 'Philly', 'Oneida', 'Murray'];
    result TEXT;
BEGIN
    IF original_customer IS NULL OR original_customer = '' THEN
        RETURN original_customer;
    END IF;

    -- Check if it's a person name (contains typical first/last name pattern)
    IF original_customer ~ '^[A-Z][a-z]+ [A-Z][a-z]+$' THEN
        -- Generate a similar person name
        RETURN mask_person_name();
    ELSIF original_customer ~* '(restaurant|dairy|farm|foods|bakery|cafe|market|store|group|company)' THEN
        -- Preserve business type
        result := business_types[1 + (random() * (array_length(business_types, 1) - 1))::integer];
        -- Add location if original had one
        IF original_customer ~* '\b(Athens|Kalamazoo|Shelbyville|Wausau|Baton Rouge|Ft Wayne|Somerset|Philly|Oneida|Murray)\b' THEN
            result := result || ' ' || locations[1 + (random() * (array_length(locations, 1) - 1))::integer];
        END IF;
    ELSE
        -- Generic business name
        result := 'Sample ' || business_types[1 + (random() * (array_length(business_types, 1) - 1))::integer];
    END IF;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to generate random person names
CREATE OR REPLACE FUNCTION mask_person_name()
RETURNS TEXT AS $$
DECLARE
    first_names TEXT[] := ARRAY['John', 'Jane', 'Michael', 'Sarah', 'David', 'Lisa', 'Robert', 'Maria', 'James', 'Jennifer', 'William', 'Linda', 'Richard', 'Patricia', 'Charles', 'Susan', 'Joseph', 'Margaret', 'Thomas', 'Dorothy'];
    last_names TEXT[] := ARRAY['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'];
BEGIN
    RETURN first_names[1 + (random() * (array_length(first_names, 1) - 1))::integer] || ' ' ||
           last_names[1 + (random() * (array_length(last_names, 1) - 1))::integer];
END;
$$ LANGUAGE plpgsql;

-- Function to mask email addresses
CREATE OR REPLACE FUNCTION mask_email(original_email TEXT)
RETURNS TEXT AS $$
DECLARE
    domains TEXT[] := ARRAY['example.com', 'testcompany.com', 'sample.org', 'demo.net', 'fakeemail.com'];
    username TEXT;
BEGIN
    IF original_email IS NULL OR original_email = '' THEN
        RETURN NULL;
    END IF;

    -- Extract username part before @
    username := split_part(original_email, '@', 1);

    -- If username is too short, generate a new one
    IF length(username) < 3 THEN
        username := 'user' || (random() * 9999)::integer;
    END IF;

    -- Return masked email
    RETURN username || '@' || domains[1 + (random() * (array_length(domains, 1) - 1))::integer];
END;
$$ LANGUAGE plpgsql;

-- Function to mask phone numbers
CREATE OR REPLACE FUNCTION mask_phone(original_phone TEXT)
RETURNS TEXT AS $$
DECLARE
    area_codes TEXT[] := ARRAY['201', '202', '203', '204', '205', '206', '207', '208', '209', '210'];
BEGIN
    IF original_phone IS NULL OR original_phone = '' THEN
        RETURN NULL;
    END IF;

    -- Generate a random 10-digit phone number
    RETURN '(' || area_codes[1 + (random() * (array_length(area_codes, 1) - 1))::integer] || ') ' ||
           (100 + (random() * 899))::text || '-' ||
           (1000 + (random() * 8999))::text;
END;
$$ LANGUAGE plpgsql;

-- Function to mask addresses
CREATE OR REPLACE FUNCTION mask_address()
RETURNS TEXT AS $$
DECLARE
    streets TEXT[] := ARRAY['Main', 'Oak', 'Pine', 'Maple', 'Cedar', 'Elm', 'Washington', 'Lincoln', 'Jefferson', 'Adams'];
    suffixes TEXT[] := ARRAY['St', 'Ave', 'Blvd', 'Dr', 'Ln', 'Way', 'Pl', 'Ct', 'Rd', 'Cir'];
BEGIN
    RETURN (100 + (random() * 9999))::text || ' ' ||
           streets[1 + (random() * (array_length(streets, 1) - 1))::integer] || ' ' ||
           suffixes[1 + (random() * (array_length(suffixes, 1) - 1))::integer];
END;
$$ LANGUAGE plpgsql;

-- Function to mask cities
CREATE OR REPLACE FUNCTION mask_city()
RETURNS TEXT AS $$
DECLARE
    cities TEXT[] := ARRAY['Springfield', 'Riverside', 'Franklin', 'Greenville', 'Bristol', 'Fairview', 'Madison', 'Georgetown', 'Salem', 'Winchester'];
BEGIN
    RETURN cities[1 + (random() * (array_length(cities, 1) - 1))::integer];
END;
$$ LANGUAGE plpgsql;

-- Function to generate generic comments
CREATE OR REPLACE FUNCTION mask_comment()
RETURNS TEXT AS $$
DECLARE
    comments TEXT[] := ARRAY[
        'Standard processing required.',
        'Please handle with care.',
        'Rush order - expedite processing.',
        'Quality check completed.',
        'Customer requested special handling.',
        'Follow standard procedures.',
        'Additional review may be needed.',
        'Contact customer for clarification.',
        'Processing in progress.',
        'Ready for next step.'
    ];
BEGIN
    RETURN comments[1 + (random() * (array_length(comments, 1) - 1))::integer];
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- PART 2: MASK SENSITIVE DATA
-- =====================================================

-- Set random seed for consistent results (optional)
-- SELECT setseed(0.12345);

-- Mask auth_user table
UPDATE auth_user
SET
    username = 'user_' || id,
    first_name = split_part(mask_person_name(), ' ', 1),
    last_name = split_part(mask_person_name(), ' ', 2),
    email = CASE WHEN email IS NOT NULL THEN mask_email(email) ELSE 'user' || id || '@example.com' END
WHERE id > 1;  -- Keep admin user unchanged if id=1

-- Mask workflow_job table
UPDATE workflow_job
SET
    name = mask_job_name(name),
    brand_name = mask_brand_name(brand_name),
    customer_name = mask_customer_name(customer_name),
    customer_email = CASE WHEN customer_email IS NOT NULL THEN mask_email(customer_email) ELSE 'masked@example.com' END,
    customer_phone = mask_phone(customer_phone),
    vrml_password = 'masked_password_' || id,
    comments = CASE WHEN comments IS NOT NULL AND comments != '' THEN mask_comment() ELSE comments END,
    instructions = CASE WHEN instructions IS NOT NULL AND instructions != '' THEN mask_comment() ELSE instructions END,
    po_number = 'PO-' || id,
    customer_po_number = 'CPO-' || id,
    user_keywords = CASE WHEN user_keywords IS NOT NULL AND user_keywords != '' THEN 'keyword1, keyword2, keyword3' ELSE user_keywords END,
    generated_keywords = CASE WHEN generated_keywords IS NOT NULL AND generated_keywords != '' THEN 'generated keyword1, generated keyword2' ELSE generated_keywords END;

-- Mask workflow_jobaddress table
UPDATE workflow_jobaddress
SET
    name = mask_person_name(),
    company = mask_brand_name(company),
    title = 'Manager',
    address1 = mask_address(),
    address2 = CASE WHEN random() < 0.3 THEN 'Suite ' || (100 + (random() * 900))::integer ELSE NULL END,
    city = mask_city(),
    state = 'CA',  -- You can randomize this too
    zip = (90000 + (random() * 9999))::text,
    country = 'USA',
    phone = mask_phone(phone),
    ext = CASE WHEN random() < 0.5 THEN (100 + (random() * 900))::text ELSE NULL END,
    email = CASE WHEN email IS NOT NULL THEN mask_email(email) ELSE 'contact@example.com' END,
    cell_phone = mask_phone(cell_phone);

-- Mask workflow_item table (if it has sensitive fields)
UPDATE workflow_item
SET
    bev_item_name = CASE WHEN bev_item_name IS NOT NULL THEN 'Product ' || id ELSE bev_item_name END,
    bev_imported_item_name = CASE WHEN bev_imported_item_name IS NOT NULL THEN 'Imported Product ' || id ELSE bev_imported_item_name END,
    description = CASE WHEN description IS NOT NULL AND description != '' THEN 'Product description for item ' || id ELSE description END
WHERE bev_item_name IS NOT NULL OR bev_imported_item_name IS NOT NULL OR description IS NOT NULL;

-- =====================================================
-- PART 3: CLEANUP AND VERIFICATION
-- =====================================================

-- Drop the masking functions (optional - comment out if you want to keep them)
-- DROP FUNCTION IF EXISTS mask_company_name();
-- DROP FUNCTION IF EXISTS mask_person_name();
-- DROP FUNCTION IF EXISTS mask_email(TEXT);
-- DROP FUNCTION IF EXISTS mask_phone(TEXT);
-- DROP FUNCTION IF EXISTS mask_address();
-- DROP FUNCTION IF EXISTS mask_city();
-- DROP FUNCTION IF EXISTS mask_comment();

-- Verify masking results
SELECT 'workflow_job masked' as table_name, COUNT(*) as records_updated
FROM workflow_job
WHERE brand_name LIKE 'Global%' OR customer_name LIKE 'Global%'

UNION ALL

SELECT 'auth_user masked' as table_name, COUNT(*) as records_updated
FROM auth_user
WHERE username LIKE 'user_%' AND id > 1

UNION ALL

SELECT 'workflow_jobaddress masked' as table_name, COUNT(*) as records_updated
FROM workflow_jobaddress
WHERE company LIKE 'Global%' OR name LIKE 'John%';

-- =====================================================
-- ADDITIONAL MASKING FOR OTHER TABLES (Uncomment as needed)
-- =====================================================

/*
-- If you have other tables with sensitive data, add them here
-- Example for a hypothetical customer table:
UPDATE customer_table
SET
    company_name = mask_company_name(),
    contact_name = mask_person_name(),
    contact_email = mask_email(contact_email),
    contact_phone = mask_phone(contact_phone),
    address = mask_address(),
    city = mask_city();

-- Example for order/invoice tables:
UPDATE order_table
SET
    customer_name = mask_company_name(),
    shipping_address = mask_address(),
    billing_address = mask_address();
*/

COMMIT;
