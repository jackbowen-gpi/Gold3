# External Database Configuration

## Overview

The application has been configured to connect to an external PostgreSQL Docker container instead of using the local database service defined in Docker Compose.

## Target Container

- **Container ID**: `c202e6b9c60b7cf3415be98762f602c3f861cd7b382e903a04763549573c2086`
- **Container Name**: `gchub_db-postgres-dev-1`
- **Host Port**: `5433` (mapped from container port `5432`)
- **Database**: `gchub_dev`
- **User**: `postgres`
- **Password**: `postgres`

## Configuration Changes

### 1. Django Settings (`settings_common.py`)

Updated the development database configuration to use the external container:

```python
DATABASES_RAW_DEV = {
    "ENGINE": os.environ.get("DEV_DB_ENGINE", "django.db.backends.postgresql"),
    "NAME": os.environ.get("DEV_DB_NAME", "gchub_dev"),          # External DB name
    "USER": os.environ.get("DEV_DB_USER", "postgres"),           # External DB user
    "PASSWORD": os.environ.get("DEV_DB_PASSWORD", "postgres"),   # External DB password
    "HOST": os.environ.get("DEV_DB_HOST", "127.0.0.1"),          # Localhost
    "PORT": os.environ.get("DEV_DB_PORT", "5433"),               # External container port
}
```

### 2. Docker Compose (`config/docker-compose.yml`)

Updated all services to use the external database:

- **Web service**: Connects to `host.docker.internal:5433`
- **Celery services**: Connect to `host.docker.internal:5433`
- **Notification daemon**: Connects to `host.docker.internal:5433`
- **Flower**: Connects to `host.docker.internal:5433`

Removed dependencies on the local `db` service since we're using an external database.

## Environment Variables

You can override the database configuration using these environment variables:

- `DEV_DB_HOST`: Database host (default: `127.0.0.1`)
- `DEV_DB_PORT`: Database port (default: `5433`)
- `DEV_DB_NAME`: Database name (default: `gchub_dev`)
- `DEV_DB_USER`: Database user (default: `postgres`)
- `DEV_DB_PASSWORD`: Database password (default: `postgres`)

## Usage

### Running the Application

```bash
# Start services (excluding the local database)
docker-compose -f config/docker-compose.yml up web redis celery notification-daemon

# Or start all services
docker-compose -f config/docker-compose.yml up
```

### Connecting to Database Directly

```bash
# Connect via host port
psql -h 127.0.0.1 -p 5433 -U postgres -d gchub_dev

# Or connect via container
docker exec -it gchub_db-postgres-dev-1 psql -U postgres -d gchub_dev
```

## Verification

Run the database configuration check:

```bash
python check_db_config.py
```

Expected output:
```
Database Configuration:
  Host: 127.0.0.1
  Port: 5433
  Database: gchub_dev
  User: postgres
  Engine: django.db.backends.postgresql

✅ Database connection successful!
  Connected to: gchub_dev as postgres
```

## Benefits

1. **External Database**: Uses existing database with real data
2. **Independent Operation**: App can run without starting local database
3. **Data Persistence**: Database data persists independently of app containers
4. **Development Flexibility**: Can connect to different database instances as needed

## Troubleshooting

### Connection Issues

1. **Container not running**:
   ```bash
   docker ps | grep gchub_db-postgres-dev-1
   ```

2. **Port not accessible**:
   ```bash
   netstat -an | findstr 5433
   ```

3. **Database credentials wrong**:
   ```bash
   docker exec gchub_db-postgres-dev-1 psql -U postgres -d gchub_dev -c "SELECT current_user;"
   ```

### Switching Back to Local Database

To revert to the local database service:

1. Uncomment the `db` service in `docker-compose.yml`
2. Update environment variables to point to `db:5432`
3. Re-enable dependencies on the `db` service
