# GOLD3 Wiki Pages

This directory contains wiki documentation for the GOLD3 Django application.

## Available Wiki Pages

### CI/CD Pipeline and Database Architecture (`ci_database_wiki.md` / `ci_database_wiki.html`)

**Comprehensive documentation covering:**

- **CI/CD Pipeline Configuration**

  - GitHub Actions matrix testing across Python 3.11, 3.12, 3.13
  - Database isolation fix for parallel job conflicts
  - Unique database names per Python version
  - CI workflow steps and optimization

- **Database Architecture**

  - PostgreSQL vs MSSQL architecture comparison
  - Django ORM vs stored procedures approach
  - Migration strategy and database objects analysis
  - Test and production database configurations

- **Development Workflow**
  - Local development setup
  - CI/CD integration details
  - Best practices for database development
  - Monitoring and maintenance guidelines

### Main Wiki Page (`wiki_page.html`)

The main landing page for GOLD3 documentation with:

- System overview and key features
- Documentation sections navigation
- Quick access links
- System statistics

### Security Features (`wiki_page2.html`)

Detailed security documentation including:

- Authentication and authorization systems
- Password security and validation
- Session management
- Security middleware and headers
- Data protection measures

## Wiki Management

### Using the Management Script

A PowerShell script is available to help manage wiki pages:

```powershell
# List all available wiki pages
.\scripts\manage_wiki_pages.ps1 -Command list

# Copy HTML pages to wiki directory
.\scripts\manage_wiki_pages.ps1 -Command copy

# Validate HTML syntax
.\scripts\manage_wiki_pages.ps1 -Command validate
```

### MediaWiki Setup

The project includes a MediaWiki setup for full wiki functionality:

1. **Start the wiki service:**

   ```bash
   docker-compose up -d wiki
   ```

2. **Access MediaWiki:**

   - URL: http://localhost:8080
   - Database: wiki_db
   - Username: wiki_user
   - Password: wiki_password

3. **Database setup:**
   ```bash
   ./scripts/setup_wiki_db.sh
   ```

## File Formats

- **`.md` files**: Markdown format for easy editing and version control
- **`.html` files**: MediaWiki format for direct import into MediaWiki
- **Management scripts**: PowerShell for Windows environments

## Recent Updates

- **September 16, 2025**: Added CI/CD Pipeline and Database Architecture documentation
- **CI Fix**: Implemented unique database names per Python version to resolve parallel job conflicts
- **Database Documentation**: Confirmed PostgreSQL ORM architecture with no stored procedures

## Contributing

When adding new wiki pages:

1. Create both `.md` and `.html` versions
2. Update the main wiki page navigation
3. Add entries to the quick access table
4. Test HTML validation with the management script
5. Update this README with new page descriptions

## Related Documentation

- `docs/POSTGRESQL_DATABASE_OBJECTS.md` - Detailed database objects analysis
- `docs/` - Additional technical documentation
- `.github/workflows/ci.yml` - CI/CD pipeline configuration
