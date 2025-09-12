-- Test the new masking functions for workflow_job table
-- This shows examples of how the data will be transformed

-- Set seed for consistent results
SELECT setseed(0.12345);

-- Test brand_name masking
SELECT
    'Original Brand Names' as test_type,
    brand_name as original,
    mask_brand_name(brand_name) as masked
FROM workflow_job
WHERE brand_name IS NOT NULL AND brand_name != ''
LIMIT 20;

-- Test job name masking
SELECT
    'Original Job Names' as test_type,
    name as original,
    mask_job_name(name) as masked
FROM workflow_job
WHERE name IS NOT NULL AND name != ''
LIMIT 20;

-- Test customer name masking
SELECT
    'Original Customer Names' as test_type,
    customer_name as original,
    mask_customer_name(customer_name) as masked
FROM workflow_job
WHERE customer_name IS NOT NULL AND customer_name != ''
LIMIT 20;

-- Show examples of pattern preservation
SELECT
    'Pattern Examples' as test_type,
    CASE
        WHEN name ~* '\b(cup|carton|bottle|can|pail|box|plate|lid|straw|napkin)\b' THEN 'Product Pattern'
        WHEN name ~* '\b(DMR|DFMS|LCRS|RTW|DMRL|LCRSSL|JCWS|PCF|PLA|KD)\b' THEN 'Campaign Pattern'
        WHEN brand_name ~* '(dairy|farm|cream|milk|cheese|butter|yogurt|ice|creamery)' THEN 'Dairy Pattern'
        ELSE 'Generic Pattern'
    END as pattern_type,
    name as original_name,
    mask_job_name(name) as masked_name,
    brand_name as original_brand,
    mask_brand_name(brand_name) as masked_brand
FROM workflow_job
WHERE (name IS NOT NULL AND name != '') OR (brand_name IS NOT NULL AND brand_name != '')
LIMIT 30;
