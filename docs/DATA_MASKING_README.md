# Data Masking for Gold3 Database

This directory contains scripts to anonymize sensitive data in your Gold3 database while preserving functionality for development and testing.

## ⚠️ IMPORTANT WARNINGS

- **NEVER run these scripts on production data!**
- **Always backup your database before running masking scripts**
- **Test on a copy of your data first**
- **Data masking is irreversible - you cannot recover original values**

## Files

- `data_masking.sql` - Main masking script that anonymizes sensitive data
- `verify_masking.sql` - Verification script to check masking results

## What Gets Masked

### Personal Information
- Names (first name, last name)
- Email addresses
- Phone numbers
- Addresses

### Business Information
- Company names
- Brand names
- Customer names
- PO numbers
- Comments and instructions

### Preserved Data
- All IDs and foreign keys (relationships maintained)
- Dates and timestamps
- Status fields
- Numeric values
- Boolean flags

## How to Use

### Step 1: Backup Your Database
```bash
# Create a backup before masking
docker exec gchub_db-postgres-dev-1 pg_dump -U postgres -d gchub_dev > backup_before_masking.sql
```

### Step 2: Run the Masking Script
```bash
# Connect to your database
docker exec -it gchub_db-postgres-dev-1 psql -U postgres -d gchub_dev

# Run the masking script
\i /path/to/data_masking.sql
```

### Step 3: Verify Results
```bash
# Run verification script
\i /path/to/verify_masking.sql
```

## Masking Examples

### Before Masking:
- Company: "ABC Beverage Company"
- Email: "john.doe@abcbeverages.com"
- Phone: "(555) 123-4567"
- Address: "123 Main St, Anytown, CA 12345"

### After Masking:
- Company: "Global Beverage Corporation"
- Email: "john.doe@example.com"
- Phone: "(201) 555-0123"
- Address: "4567 Oak Ave, Springfield, CA 90001"

## Customization Options

### Modify Company Name Generation
Edit the `mask_company_name()` function to change the prefixes, products, and suffixes used for generating company names.

### Add More Tables
To mask additional tables, add UPDATE statements to the main script:

```sql
UPDATE your_table
SET
    sensitive_field1 = mask_function1(sensitive_field1),
    sensitive_field2 = mask_function2(sensitive_field2);
```

### Adjust Masking Intensity
- For lighter masking: Keep some original structure (e.g., preserve email domains)
- For heavier masking: Replace all values with completely random data
- For testing: Use predictable patterns (e.g., "masked_" + id)

## Functions Available

- `mask_company_name()` - Generates realistic company names
- `mask_person_name()` - Generates realistic person names
- `mask_email(text)` - Masks email addresses while preserving format
- `mask_phone(text)` - Generates valid phone numbers
- `mask_address()` - Generates realistic addresses
- `mask_city()` - Generates city names
- `mask_comment()` - Generates generic comments

## Testing the Masked Data

After masking, test that your application still works:

1. User authentication
2. Order/job processing
3. Email notifications
4. Address validation
5. Search functionality
6. Reporting features

## Troubleshooting

### If masking fails:
1. Check for foreign key constraints
2. Ensure you have proper permissions
3. Verify the database connection

### If data looks wrong:
1. Check the random seed setting
2. Review the masking functions
3. Run verification script

### To undo masking:
Unfortunately, masking is irreversible. Restore from backup if needed.

## Security Considerations

- Masked data is still useful for development/testing
- Original data patterns are preserved (length, format)
- Relationships between tables are maintained
- No real PII remains in the database

## Performance Notes

- Masking large tables may take time
- Consider running during off-hours
- Monitor database performance during masking
- VACUUM after masking to reclaim space
