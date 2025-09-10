# Redis (broker)

Redis is used as the Celery broker in this project. It handles task message transport between producers (web) and consumers (workers).

## Service name
- `redis` in `docker-compose.yml`.

## Common checks
- Verify Redis is running:
```pwsh
docker-compose ps redis
docker-compose logs redis
```

## Connect to Redis from a container
```pwsh
docker-compose exec redis redis-cli ping
# Should reply: PONG
```

## Notes
- Make sure `CELERY_BROKER_URL` points to the `redis` service (e.g. `redis://redis:6379/0`).

## Links
- Redis: https://redis.io/
