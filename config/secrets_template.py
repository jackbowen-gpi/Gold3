"""
Secure configuration file for sensitive data.
This file should NOT be committed to version control.
Copy this file to config/secrets.py and populate with actual values.
"""

import os

# =============================================================================
# SECURITY WARNING: This file contains sensitive information!
# =============================================================================
# - DO NOT commit this file to version control
# - Keep it secure and limit access
# - Use strong, unique passwords/keys
# - Rotate credentials regularly

# Django Secret Key
# Generate a new one for production: python -c "import secrets; print(secrets.token_urlsafe(50))"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION")

# Database Credentials
DATABASE_CREDENTIALS = {
    "production": {
        "NAME": os.environ.get("DB_NAME", "thundercuddles"),
        "USER": os.environ.get("DB_USER", "thundercuddles"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "CHANGE_THIS"),
        "HOST": os.environ.get("DB_HOST", "172.23.8.73"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    },
    "development": {
        "NAME": os.environ.get("DEV_DB_NAME", "gchub_dev"),
        "USER": os.environ.get("DEV_DB_USER", "gchub"),
        "PASSWORD": os.environ.get("DEV_DB_PASSWORD", "gchub"),
        "HOST": os.environ.get("DEV_DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DEV_DB_PORT", "5438"),
    },
}

# FTP Credentials
FTP_CREDENTIALS = {
    "fusion_flexo": {
        "USERNAME": os.environ.get("FUSION_FLEXO_FTP_USER", "fusion_flexo"),
        "PASSWORD": os.environ.get("FUSION_FLEXO_FTP_PASSWORD", "CHANGE_THIS"),
        "HOST": os.environ.get("FUSION_FLEXO_FTP_HOST", "ftp.fusionflexo.com"),
        "PORT": os.environ.get("FUSION_FLEXO_FTP_PORT", "21"),
    },
    "ftp1": {
        "USERNAME": os.environ.get("FTP1_USER", "ftp_user"),
        "PASSWORD": os.environ.get("FTP1_PASSWORD", "CHANGE_THIS"),
        "HOST": os.environ.get("FTP1_HOST", "ftp.example.com"),
        "PORT": os.environ.get("FTP1_PORT", "21"),
    },
    "ftp2": {
        "USERNAME": os.environ.get("FTP2_USER", "ftp_user"),
        "PASSWORD": os.environ.get("FTP2_PASSWORD", "CHANGE_THIS"),
        "HOST": os.environ.get("FTP2_HOST", "ftp.example.com"),
        "PORT": os.environ.get("FTP2_PORT", "21"),
    },
    "ftp3": {
        "USERNAME": os.environ.get("FTP3_USER", "ftp_user"),
        "PASSWORD": os.environ.get("FTP3_PASSWORD", "CHANGE_THIS"),
        "HOST": os.environ.get("FTP3_HOST", "ftp.example.com"),
        "PORT": os.environ.get("FTP3_PORT", "21"),
    },
}

# API Keys and External Service Credentials
API_CREDENTIALS = {
    "fedex": {
        "test": {
            "ACCOUNT_NUMBER": os.environ.get("FEDEX_TEST_ACCOUNT", "123456789"),
            "METER_NUMBER": os.environ.get("FEDEX_TEST_METER", "123456789"),
            "PASSWORD": os.environ.get("FEDEX_TEST_PASSWORD", "CHANGE_THIS"),
            "KEY": os.environ.get("FEDEX_TEST_KEY", "CHANGE_THIS"),
        },
        "production": {
            "ACCOUNT_NUMBER": os.environ.get("FEDEX_ACCOUNT", "123456789"),
            "METER_NUMBER": os.environ.get("FEDEX_METER", "123456789"),
            "PASSWORD": os.environ.get("FEDEX_PASSWORD", "CHANGE_THIS"),
            "KEY": os.environ.get("FEDEX_KEY", "CHANGE_THIS"),
        },
    }
}

# Email Configuration
EMAIL_CREDENTIALS = {
    "HOST": os.environ.get("EMAIL_HOST", "localhost"),
    "PORT": int(os.environ.get("EMAIL_PORT", "587")),
    "USERNAME": os.environ.get("EMAIL_USER", ""),
    "PASSWORD": os.environ.get("EMAIL_PASSWORD", ""),
    "USE_TLS": os.environ.get("EMAIL_USE_TLS", "True").lower() == "true",
    "USE_SSL": os.environ.get("EMAIL_USE_SSL", "False").lower() == "true",
}

# Other Service Credentials
SERVICE_CREDENTIALS = {
    "redis": {
        "HOST": os.environ.get("REDIS_HOST", "localhost"),
        "PORT": int(os.environ.get("REDIS_PORT", "6379")),
        "PASSWORD": os.environ.get("REDIS_PASSWORD", ""),
        "DB": int(os.environ.get("REDIS_DB", "0")),
    },
    "celery": {
        "BROKER_URL": os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        "RESULT_BACKEND": os.environ.get(
            "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
        ),
    },
}

# Security Settings
SECURITY_SETTINGS = {
    "ALLOWED_HOSTS": os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(","),
    "CSRF_TRUSTED_ORIGINS": os.environ.get(
        "CSRF_TRUSTED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000"
    ).split(","),
    "SECURE_SSL_REDIRECT": os.environ.get("SECURE_SSL_REDIRECT", "False").lower()
    == "true",
    "SESSION_COOKIE_SECURE": os.environ.get("SESSION_COOKIE_SECURE", "False").lower()
    == "true",
    "CSRF_COOKIE_SECURE": os.environ.get("CSRF_COOKIE_SECURE", "False").lower()
    == "true",
}

# Environment Detection
ENVIRONMENT = os.environ.get("DJANGO_ENV", "development").lower()
IS_PRODUCTION = ENVIRONMENT == "production"
IS_DEVELOPMENT = ENVIRONMENT == "development"
IS_TESTING = ENVIRONMENT == "testing"
