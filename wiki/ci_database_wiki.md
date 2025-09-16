# CI/CD Pipeline and Database Architecture

## Overview

This document covers the CI/CD pipeline configuration and database architecture decisions for the GOLD3 Django application, including recent fixes for parallel testing conflicts and documentation of the PostgreSQL database structure.

## 🔄 CI/CD Pipeline Configuration

### GitHub Actions Matrix Testing

The CI pipeline uses a matrix strategy to test across multiple Python versions simultaneously:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
```

#### Database Isolation Fix

**Problem**: Multiple Python versions running in parallel were using the same database name (`gchub_test`), causing migration conflicts and "relation already exists" errors.

**Solution**: Implemented unique database names per Python version:

```yaml
# Before (causing conflicts)
echo "TEST_PG_NAME=gchub_test" >> $GITHUB_ENV

# After (unique per job)
echo "TEST_PG_NAME=gchub_test_${{ matrix.python-version }}" >> $GITHUB_ENV
```

**Result**: Each Python version now gets its own isolated database:

- Python 3.11 → `gchub_test_3.11`
- Python 3.12 → `gchub_test_3.12`
- Python 3.13 → `gchub_test_3.13`

### CI Workflow Steps

1. **Setup Python** - Install specified Python version
2. **Cache Dependencies** - Speed up pip installs
3. **Install System Dependencies** - PostgreSQL client libraries
4. **Install Python Packages** - From requirements files
5. **Configure Database** - Set unique database name per job
6. **Reset Database** - Clean state for each test run
7. **Run Migrations** - Apply Django schema changes
8. **Run Tests** - Execute test suite with coverage
9. **Security Scans** - Bandit and Safety vulnerability checks

### Benefits of Multi-Version Testing

- **Compatibility Assurance**: Validates Django 5.2.6 works across Python versions
- **Future-Proofing**: Catches issues before production deployment
- **Dependency Validation**: Ensures all packages work with different Python versions
- **Performance Insights**: Identifies performance differences between versions
- **Migration Planning**: Smooth transition path for Python upgrades

## 🗄️ Database Architecture

### PostgreSQL vs MSSQL Architecture

The GOLD3 application uses **PostgreSQL as the primary database** with limited MSSQL integration for external systems.

#### PostgreSQL (Primary Database)

**Architecture Approach**: Django ORM + Standard SQL

- ✅ **Django Migrations**: Standard schema management
- ✅ **Django ORM**: Model-based database operations
- ✅ **Raw SQL**: Limited usage for complex queries
- ❌ **No Stored Procedures**: Not used in PostgreSQL
- ❌ **No Database Functions**: Not implemented
- ❌ **No Triggers**: Not utilized

#### MSSQL (External Integration)

**Architecture Approach**: Raw SQL queries for external data access

Located in `gchub_db/apps/workflow/etools.py`:

```python
# External MSSQL database connection
cursor.execute("""
    SELECT TOP 5 * FROM tb_FSAR_Data_SampArtReq
    WHERE Job_Status = 'New'
""")
```

### Database Objects Analysis

#### No PostgreSQL Stored Procedures

After comprehensive codebase analysis, **zero PostgreSQL stored procedures** were found:

- **Django Models**: Handle business logic in Python
- **Django Managers**: Custom query methods
- **Django Signals**: Event-driven operations
- **Raw SQL**: Only for external MSSQL integration

#### Migration Strategy

```python
# Example migration creating PlantBevController model
operations = [
    migrations.CreateModel(
        name="PlantBevController",
        fields=[
            ("id", models.BigAutoField(primary_key=True)),
            ("plant", models.ForeignKey("workflow.plant")),
            ("user", models.ForeignKey(settings.AUTH_USER_MODEL)),
        ],
        options={
            "db_table": "workflow_plant_bev_controller",
        },
    ),
]
```

### Database Configuration

#### Test Settings (`gchub_db/test_settings.py`)

```python
# Environment-based database configuration
TEST_PG_NAME = os.environ.get("TEST_PG_NAME")
if TEST_PG_NAME:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": TEST_PG_NAME,
            "USER": TEST_PG_USER,
            "PASSWORD": TEST_PG_PASSWORD,
            "HOST": TEST_PG_HOST,
            "PORT": TEST_PG_PORT,
            "TEST": {"NAME": TEST_PG_NAME},
        }
    }
```

#### Production Settings

- PostgreSQL 15 with connection pooling
- Database backups and replication
- Monitoring and performance optimization
- Security hardening (SSL, authentication)

## 🔧 Development Workflow

### Local Development Setup

1. **Database**: PostgreSQL 15 via Docker
2. **Python**: Version 3.11+ (matches CI matrix)
3. **Dependencies**: Managed via requirements-dev.txt
4. **Migrations**: Django makemigrations/migrate
5. **Testing**: pytest with coverage reporting

### CI/CD Integration

- **Trigger**: Push/PR to main/jb branches
- **Services**: PostgreSQL 15 container per job
- **Caching**: pip dependencies and system packages
- **Artifacts**: Coverage reports and security scans
- **Notifications**: GitHub status checks

## 📊 Monitoring and Maintenance

### Database Health Checks

- Connection pool monitoring
- Query performance analysis
- Migration status verification
- Backup integrity validation

### CI/CD Metrics

- Test execution time per Python version
- Coverage percentage trends
- Security scan results
- Migration success rates

## 🚀 Best Practices

### Database Development

1. **Use Django ORM** for standard operations
2. **Avoid raw SQL** unless necessary
3. **Test migrations** on all Python versions
4. **Document schema changes** thoroughly
5. **Monitor query performance** regularly

### CI/CD Optimization

1. **Parallel execution** with isolated databases
2. **Dependency caching** for faster builds
3. **Security scanning** on every commit
4. **Coverage reporting** for quality metrics
5. **Matrix testing** for compatibility assurance

## 📚 Related Documentation

- [[Database Schema Documentation]] - Detailed table structures
- [[Django Apps Documentation]] - Application modules
- [[API Documentation]] - REST endpoints
- [[Security Features]] - Authentication and authorization
- [[Testing & Quality Assurance]] - Test coverage and QA processes

---

_Last updated: September 16, 2025_
_CI Fix implemented: Unique database names per Python version_
_Database documentation: PostgreSQL ORM architecture confirmed_
