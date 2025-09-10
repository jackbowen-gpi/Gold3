# Docker Guide for Gold3

## What is Docker?
Docker is a platform that allows you to package applications and their dependencies into containers. Containers are lightweight, portable, and ensure your app runs the same way everywhere—on your laptop, a server, or the cloud.

## Benefits of Using Docker
- **Consistency:** Eliminates "works on my machine" problems by packaging everything needed to run the app.
- **Isolation:** Keeps your app and its dependencies isolated from other software on your system.
- **Portability:** Run the same container image on any system with Docker installed.
- **Easy Setup:** Onboard new developers quickly—no need to install Python, Postgres, or other dependencies manually.
- **Scalability:** Easily scale and orchestrate containers in production with tools like Docker Compose or Kubernetes.

## How This Project Uses Docker
This project provides a `Dockerfile` to build the Django app and a `docker-compose.yml` to run the app with its dependencies (like Postgres) in containers.

### Typical Workflow
1. **Build the image:**
   ```sh
   docker build -t gold3 .
   ```
2. **Run the app (standalone):**
   ```sh
   docker run -it --rm -p 8000:8000 gold3
   ```
3. **Run with Docker Compose (recommended):**
   - Make sure you have a `docker-compose.yml` (see below).
   - Start all services:
     ```sh
     docker-compose up --build
     ```
   - Stop services:
     ```sh
     docker-compose down
     ```

### Environment Variables
- You may need to set environment variables for database credentials, Django settings, etc. Use a `.env` file or set them in `docker-compose.yml`.

### Database Migrations
After starting the containers, run migrations:
```sh
docker-compose exec web python manage.py migrate
```

### Static Files
If you use Django static files, you may need to run:
```sh
docker-compose exec web python manage.py collectstatic --noinput
```

## Troubleshooting
- **Port conflicts:** Make sure port 8000 (or your chosen port) is free.
- **File permissions:** Some files may be owned by root inside the container. Use Docker volumes for development.
- **Database connection errors:** Ensure the database container is healthy and the credentials match your Django settings.

## Further Reading
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Django + Docker Best Practices](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)

---

## Example docker-compose.yml
```yaml
version: '3.9'
services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: gchub_dev
      POSTGRES_USER: gchub
      POSTGRES_PASSWORD: gchub
    ports:
      - "5433:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```
