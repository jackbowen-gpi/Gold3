# Django Settings Reorganization

This document describes the reorganized Django settings structure for the Gold3 project, which provides better security, maintainability, and environment management.

## Overview

The settings have been reorganized into a modular structure that separates:

- **Base settings**: Common configuration shared across all environments
- **Environment-specific settings**: Development, staging, and production configurations
- **Secrets management**: Centralized secure storage of sensitive data
- **Local overrides**: Optional local settings for development

## File Structure

```
config/
├── settings.py              # Main orchestration file
├── settings_base.py         # Common settings for all environments
├── settings_development.py  # Development environment settings
├── settings_production.py   # Production environment settings
├── settings_staging.py      # Staging environment settings (optional)
├── settings_local.py        # Local overrides (optional, not in git)
├── secrets.py               # Sensitive data (NOT in git)
├── secrets_template.py      # Template for secrets.py
└── settings_common.py       # Legacy common settings (being phased out)
```

## Key Features

### 1. Environment-Based Configuration

- Set `DJANGO_ENV` environment variable to control which settings are loaded
- Supported environments: `development`, `staging`, `production`
- Default: `development`

### 2. Secure Secrets Management

- All sensitive data moved to `config/secrets.py`
- File is NOT committed to version control
- Template provided in `config/secrets_template.py`
- Environment variable fallbacks for container deployments

### 3. Environment Variable Support

- All settings can be overridden via environment variables
- Supports Docker/container deployments
- Database URL support via `DATABASE_URL`
- AWS S3 configuration for static files

## Setup Instructions

### 1. Initial Setup

```bash
# Copy the secrets template
cp config/secrets_template.py config/secrets.py

# Edit secrets.py with your actual credentials
# NEVER commit secrets.py to version control
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your environment-specific values
```

### 3. Environment Variables

Set the following environment variables:

```bash
# Required
export DJANGO_ENV=development  # or staging, production
export DJANGO_DEBUG=true       # or false for production

# Optional - Database
export DATABASE_URL=postgresql://user:pass@host:port/db

# Optional - Redis/Celery
export REDIS_URL=redis://localhost:6379/0

# Optional - AWS S3 (for production static files)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_STORAGE_BUCKET_NAME=your_bucket
```

## Secrets Configuration

The `config/secrets.py` file contains all sensitive data:

```python
# Database Credentials
DATABASE_CREDENTIALS = {
    'PRODUCTION': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'thundercuddles',
        'USER': 'thundercuddles',
        'PASSWORD': 'your_production_password',
        'HOST': '172.23.8.73',
        'PORT': '5432',
    },
    'DEVELOPMENT': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gchub_dev',
        'USER': 'gchub',
        'PASSWORD': 'your_dev_password',
        'HOST': '127.0.0.1',
        'PORT': '5438',
    }
}

# FedEx API Credentials
FEDEX_CREDENTIALS = {
    'PRODUCTION': {
        'ACCOUNT_NUM': '248430818',
        'METER_NUM': '1301709',
        'PASSWORD': 'your_fedex_password',
        'KEY': 'your_fedex_key'
    }
}

# FTP Credentials
FTP_CREDENTIALS = {
    'FUSION_FLEXO': {
        'HOST': 'exchange.graphicpkg.com',
        'USERNAME': 'fusionflexo',
        'PASSWORD': 'your_ftp_password',
        'ROOT_DIR': 'togpi'
    }
}

# Django SECRET_KEY
SECRET_KEY = 'your_django_secret_key'
```

## Migration from Old Settings

### What Changed

1. **Hardcoded secrets removed**: All passwords, API keys, and sensitive data moved to `secrets.py`
2. **Modular structure**: Settings split into logical, environment-specific files
3. **Environment variables**: Support for configuration via environment variables
4. **Security improvements**: Sensitive data centralized and excluded from version control

### Backward Compatibility

- Legacy `config/settings_common.py` still works but is being phased out
- Existing environment variables continue to work
- No breaking changes to application code

## Security Best Practices

### 1. Never Commit Secrets

```bash
# Add to .gitignore
config/secrets.py
.env
```

### 2. Use Environment Variables in Production

```bash
# Production deployment
export DJANGO_ENV=production
export DJANGO_DEBUG=false
export DATABASE_URL=postgresql://...
export REDIS_URL=redis://...
```

### 3. Rotate Secrets Regularly

- Generate new Django `SECRET_KEY` for each deployment
- Rotate API keys and passwords periodically
- Use different credentials for each environment

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'config.secrets'**

   - Ensure `config/secrets.py` exists and contains valid Python
   - Check file permissions

2. **Settings not loading**

   - Verify `DJANGO_ENV` environment variable is set correctly
   - Check that all required settings files exist

3. **Database connection fails**
   - Verify database credentials in `secrets.py`
   - Check `DATABASE_URL` environment variable
   - Ensure database server is accessible

### Debug Mode

Enable debug logging:

```bash
export DJANGO_LOG_LEVEL=DEBUG
```

## Development Workflow

1. **Local Development**:

   ```bash
   export DJANGO_ENV=development
   export DJANGO_DEBUG=true
   python manage.py runserver
   ```

2. **Production Deployment**:

   ```bash
   export DJANGO_ENV=production
   export DJANGO_DEBUG=false
   python manage.py collectstatic
   python manage.py migrate
   ```

3. **Testing**:
   ```bash
   export DJANGO_ENV=development
   python manage.py test
   ```

## Future Improvements

- [ ] Add settings validation
- [ ] Implement settings caching
- [ ] Add support for multiple database configurations
- [ ] Create automated secrets rotation
- [ ] Add settings documentation generation
