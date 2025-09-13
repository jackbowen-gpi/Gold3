# MediaWiki Setup for Gold3

## Quick Start

1. **Start the wiki service:**

   ```bash
   docker-compose up -d wiki
   ```

2. **Wait for setup to complete** (about 30 seconds for database setup)

3. **Access MediaWiki:**
   - URL: http://localhost:8080
   - First time setup will guide you through creating an admin account

## Database Configuration

- **Database:** PostgreSQL (shared with main app)
- **Database Name:** wiki_db
- **Username:** wiki_user
- **Password:** wiki_password
- **Host:** db (internal Docker network)

## File Locations

- **LocalSettings.php:** `./wiki/LocalSettings.php`
- **Wiki Data:** Docker volume `wiki_data`
- **Database Setup Script:** `./scripts/setup_wiki_db.sh`

## Migration from Old MediaWiki

If you have an existing MediaWiki installation:

1. **Export from old wiki:**

   ```sql
   mysqldump -u username -p old_wiki_db > wiki_backup.sql
   ```

2. **Import to new wiki:**

   ```bash
   docker exec -i gold3_db_1 psql -U wiki_user -d wiki_db < wiki_backup.sql
   ```

3. **Update LocalSettings.php** with any custom configurations from your old wiki

## Useful Commands

```bash
# Start wiki
docker-compose up -d wiki

# Stop wiki
docker-compose stop wiki

# View wiki logs
docker-compose logs wiki

# Restart wiki
docker-compose restart wiki

# Remove wiki (keeps data)
docker-compose rm wiki

# Remove wiki and data
docker-compose down -v wiki
```

## Troubleshooting

- **Can't access wiki:** Check if port 8080 is available
- **Database connection error:** Wait longer for database setup, or check logs
- **Permission errors:** Ensure wiki_data volume has correct permissions

## Security Notes

- Change default passwords in production
- Update $wgSecretKey and remove $wgUpgradeKey after setup
- Configure proper user permissions
- Enable SSL/HTTPS in production
