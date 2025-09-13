# Django Development Tools Setup

This document describes the Django Extensions and Django Debug Toolbar tools that have been added to enhance the development experience for the Gold3 Django project.

## Django Extensions

**Version:** 4.1
**Purpose:** Collection of custom extensions for Django
**Installation:** Already installed in `config/requirements.txt`

### Key Features

Django Extensions provides useful management commands and utilities for Django development:

#### Management Commands

- `shell_plus`: Enhanced Django shell with auto-imported models and useful functions
- `runserver_plus`: Enhanced development server with Werkzeug debugger
- `graph_models`: Generate visual diagrams of your Django models
- `show_urls`: Display all URL patterns in your project
- `validate_templates`: Validate Django templates for syntax errors
- `clear_cache`: Clear Django's cache
- `reset_db`: Reset the database (use with caution!)
- `export_emails`: Export email addresses from auth.User
- `print_settings`: Pretty-print Django settings

#### Usage Examples

```bash
# Enhanced shell with auto-imported models
python manage.py shell_plus

# Enhanced development server
python manage.py runserver_plus

# Generate model diagram (requires graphviz)
python manage.py graph_models -a -o models.png

# Show all URL patterns
python manage.py show_urls

# Validate templates
python manage.py validate_templates
```

### Configuration

Django Extensions is already configured in `gchub_db/settings.py`:

```python
INSTALLED_APPS = (
    # ... other apps ...
    "django_extensions",
    # ... more apps ...
)
```

## Django Debug Toolbar

**Version:** 4.4.6
**Purpose:** Configurable set of panels for debugging Django applications
**Installation:** Added to `config/requirements.txt`

### Key Features

Django Debug Toolbar provides debugging information and performance metrics in development:

#### Available Panels

- **SQL**: Shows SQL queries executed, execution time, and EXPLAIN output
- **Timer**: Request timing information
- **Settings**: Django settings and their values
- **Headers**: Request and response headers
- **Request**: Request variables (GET, POST, cookies, session, etc.)
- **Templates**: Templates used and their context
- **Cache**: Cache usage statistics
- **Signals**: Django signals and their handlers
- **Logging**: Application logging output
- **Versions**: Versions of installed packages
- **Static Files**: Static file information

### Configuration

Django Debug Toolbar is configured in `gchub_db/settings.py`:

```python
# Added to INSTALLED_APPS
INSTALLED_APPS = (
    # ... other apps ...
    "debug_toolbar",
    # ... more apps ...
)

# Added to MIDDLEWARE (early in the chain)
MIDDLEWARE = (
    # ... other middleware ...
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    # ... more middleware ...
)

# INTERNAL_IPS for toolbar visibility (DEBUG mode only)
if DEBUG:
    INTERNAL_IPS = [
        "127.0.0.1",
        "localhost",
    ]
```

### URL Configuration

Debug toolbar URLs are configured in `config/urls.py`:

```python
# Django Debug Toolbar URLs - only in DEBUG mode
if getattr(settings, "DEBUG", False):
    try:
        import debug_toolbar
        urlpatterns.insert(0, url(r"^__debug__/", include(debug_toolbar.urls)))
    except ImportError:
        # debug_toolbar not installed, skip
        pass
```

### Usage

1. **Enable DEBUG mode** in your Django settings
2. **Access your Django application** in a browser
3. **Look for the toolbar** on the right side of the page (it appears as a dark panel)
4. **Click on different panels** to view debugging information

The toolbar will only appear when:
- `DEBUG = True` in Django settings
- Your IP address is in `INTERNAL_IPS` (configured for localhost)
- You're accessing the site from an allowed IP

### Security Notes

- **Never enable in production** - the debug toolbar exposes sensitive information
- Only appears when `DEBUG = True`
- Only visible from IP addresses listed in `INTERNAL_IPS`
- Automatically disabled in production environments

### Troubleshooting

If the toolbar doesn't appear:
1. Verify `DEBUG = True` in settings
2. Check that your IP is in `INTERNAL_IPS`
3. Ensure you're accessing via `127.0.0.1` or `localhost` (not external IP)
4. Check browser console for JavaScript errors
5. Verify the package is installed: `pip list | grep debug`

## Installation

To install the new packages:

```bash
# Install from requirements.txt
pip install -r config/requirements.txt

# Or install individually
pip install django-debug-toolbar==4.4.6
```

## Development Workflow

With these tools installed, your development workflow is enhanced:

1. **Use `runserver_plus`** for better error pages and debugging
2. **Use the Debug Toolbar** to monitor SQL queries, templates, and performance
3. **Use `shell_plus`** for interactive debugging with auto-imported models
4. **Use `show_urls`** to verify URL configuration
5. **Use `graph_models`** to visualize your data model relationships

## Best Practices

- Always disable debug tools in production
- Use the toolbar to identify N+1 query problems
- Monitor template rendering performance
- Check cache hit/miss ratios
- Review signal usage for performance bottlenecks

## Additional Resources

- [Django Extensions Documentation](https://django-extensions.readthedocs.io/)
- [Django Debug Toolbar Documentation](https://django-debug-toolbar.readthedocs.io/)
- [Django Debug Toolbar GitHub](https://github.com/jazzband/django-debug-toolbar)</content>
<parameter name="filePath">c:\Dev\Gold3\docs\DEV_TOOLS_README.md
