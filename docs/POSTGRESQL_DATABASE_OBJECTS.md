# PostgreSQL Database Objects Documentation

## Overview

This Django application **does not use PostgreSQL stored procedures or database functions**. The database architecture relies on Django's ORM and standard SQL queries instead of stored procedures.

## Key Findings

### No Stored Procedures Found

After comprehensive analysis of the codebase, **no PostgreSQL stored procedures** were found:

- ✅ Django migrations (standard schema changes)
- ✅ Django ORM queries (model-based database operations)
- ✅ Raw SQL queries (limited usage for external databases)
- ❌ **No PostgreSQL stored procedures**
- ❌ **No PostgreSQL functions**
- ❌ **No database triggers**

### Database Architecture

#### 1. Django ORM (Primary Approach)

```python
# Standard Django model operations
user = User.objects.get(id=1)
jobs = Job.objects.filter(status='active')
```

#### 2. Raw SQL Queries (Limited Usage)

Located in `gchub_db/apps/workflow/etools.py` for external MSSQL database:

```python
# Raw SQL for external MSSQL database (not PostgreSQL)
cursor.execute("SELECT TOP 5 * FROM tb_FSAR_Data_SampArtReq WHERE Job_Status = 'New'")
```

#### 3. Django Migrations (Schema Management)

```python
# Standard Django migration
operations = [
    migrations.CreateModel(
        name='PlantBevController',
        fields=[...]
    ),
]
```

## PostgreSQL vs MSSQL Comparison

### PostgreSQL Approach (This Application)

```sql
-- No stored procedures used
-- Schema changes via Django migrations
-- Business logic in Python/Django
-- Database used primarily for data storage
```

### MSSQL Approach (Your Background)

```sql
-- Stored procedures common
CREATE PROCEDURE GetActiveJobs
AS
BEGIN
    SELECT * FROM Jobs WHERE Status = 'Active'
END

-- Triggers for business logic
CREATE TRIGGER UpdateJobTimestamp
ON Jobs
AFTER UPDATE
AS
BEGIN
    UPDATE Jobs SET UpdatedAt = GETDATE() WHERE Id = (SELECT Id FROM inserted)
END
```

## Why No Stored Procedures?

### Django Philosophy

1. **ORM-Centric**: Django encourages model-based database operations
2. **Python Business Logic**: Complex logic lives in Python, not database
3. **Migration-Based Schema**: Schema changes through migrations, not procedures
4. **Database Agnostic**: Code works across different database backends

### Benefits of Current Approach

- ✅ **Database Agnostic**: Same code works on PostgreSQL, MySQL, SQLite
- ✅ **Version Control**: Schema changes tracked in Git via migrations
- ✅ **Testing**: Business logic testable in Python unit tests
- ✅ **Maintainability**: Logic centralized in application code
- ✅ **Debugging**: Easier to debug Python code than stored procedures

## Database Objects Actually Used

### Tables (via Django Models)

- `workflow_plant_bev_controller` (created via migration)
- Standard Django tables (auth_user, django_session, etc.)
- Application-specific tables for jobs, items, etc.

### Indexes (via Django Migrations)

```python
# Migration creating indexes
migrations.AddIndex(
    model_name='job',
    index=models.Index(fields=['status', 'created_date'], name='job_status_created_idx'),
),
```

### Constraints (via Django Models)

```python
# Model-level constraints
class Meta:
    constraints = [
        models.UniqueConstraint(fields=['plant', 'user'], name='unique_plant_user')
    ]
```

## Migration History

Recent migrations show standard Django operations:

- `0049_plantbevcontroller_and_more`: Creates PlantBevController model
- Standard field additions, index creation, constraint modifications
- No stored procedure creation

## Recommendations

### For PostgreSQL Development

1. **Use Django ORM** for most operations
2. **Raw SQL only when necessary** (performance-critical queries)
3. **Migrations for schema changes**
4. **Python functions for business logic**

### If Stored Procedures Needed

```python
# Option 1: Raw SQL in Django
from django.db import connection

def get_active_jobs():
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM jobs WHERE status = 'active'")
        return cursor.fetchall()

# Option 2: Database functions (rare in Django)
# CREATE FUNCTION get_active_jobs() RETURNS TABLE(...) AS $$
# BEGIN
#     RETURN QUERY SELECT * FROM jobs WHERE status = 'active';
# END;
# $$ LANGUAGE plpgsql;
```

## Testing Database

The test database is a standard PostgreSQL instance with:

- **No stored procedures**
- **Standard Django test tables**
- **Same schema as production**
- **Isolated from production data**

## Conclusion

This application follows **Django best practices** by avoiding stored procedures and using the ORM for database operations. The architecture is **database-agnostic** and **maintainable**, though it may feel different if you're coming from an MSSQL environment where stored procedures are more common.

**No PostgreSQL stored procedures to document** - the application uses Django's standard database patterns instead.</content>
<parameter name="filePath">c:\Dev\Gold3\docs\POSTGRESQL_DATABASE_OBJECTS.md
