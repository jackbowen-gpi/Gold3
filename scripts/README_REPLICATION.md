# Database Replication System

This system provides efficient methods to replicate data from the `gchub_db` PostgreSQL container to the `gold3-db-1` container for development and testing purposes.

## Quick Start

### Manual Replication (Recommended for one-time imports)

Run the batch script from the project root:

```batch
scripts\replicate-db.bat
```

Or specify custom parameters:

```batch
scripts\replicate-db.bat gchub_db-postgres-dev-1 gold3-db-1 direct
```

### Using Docker Compose

1. **Automatic replication on startup** (for fresh databases):
   ```batch
   docker-compose -f docker-compose.yml -f config\docker-compose.replicate.yml up -d
   ```

2. **Manual replication service**:
   ```batch
   docker-compose -f docker-compose.yml -f config\docker-compose.replicate.yml --profile replicator up db-replicator
   ```

### Direct Python Script

```batch
python scripts/db_replicate.py --source gchub_db-postgres-dev-1 --target gold3-db-1 --method direct --verbose
```

## Replication Methods

### 1. Direct Method (Recommended)
- **Pros**: Fastest, no intermediate files, handles large datasets efficiently
- **Cons**: Requires both containers running simultaneously
- **Use case**: Development environments, regular data refreshes

### 2. Compressed Dump Method
- **Pros**: Creates reusable backup files, can be used for backups
- **Cons**: Requires disk space for dump file, slower for very large databases
- **Use case**: Creating backups, one-time migrations

### 3. Standard Dump Method
- **Pros**: Standard PostgreSQL format, compatible with pg_restore
- **Cons**: Largest file size, slowest method
- **Use case**: When you need standard SQL dumps

## Configuration

### Environment Variables

- `SOURCE_DB`: Source database container name (default: `gchub_db-postgres-dev-1`)
- `TARGET_DB`: Target database container name (default: `gold3-db-1`)
- `POSTGRES_PASSWORD`: Database password (read from environment)

### Script Parameters

- `--source`: Source container name
- `--target`: Target container name
- `--method`: Replication method (`direct`, `compressed`, `standard`)
- `--verbose`: Enable detailed logging
- `--exclude-tables`: Comma-separated list of tables to exclude

## Troubleshooting

### Common Issues

1. **Container not found**: Ensure both source and target containers are running
   ```batch
   docker ps
   ```

2. **Permission denied**: Check that the script has execute permissions
   ```batch
   icacls scripts\replicate-db.bat
   ```

3. **Database connection failed**: Verify database credentials and network connectivity
   ```batch
   docker exec -it gold3-db-1 psql -U postgres -d gold3 -c "SELECT 1;"
   ```

### Logs

Check replication logs in:
- Console output (when using `--verbose`)
- Docker container logs: `docker logs <container_name>`

## Files Created

- `scripts/db_replicate.py`: Main replication script
- `scripts/init-replicate.ps1`: PowerShell initialization script
- `scripts/replicate-db.bat`: Windows batch script for manual runs
- `config/docker-compose.replicate.yml`: Docker Compose override for replication
- `scripts/init-replicate.sh`: Bash initialization script (Linux/Mac)
