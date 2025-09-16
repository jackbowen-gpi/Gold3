# Dockerfile for Gold3 Django app
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies (including ODBC for pyodbc and PrinceXML for PDF generation)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    unixodbc-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install PrinceXML for high-quality PDF generation
RUN wget -O prince.deb https://www.princexml.com/download/prince_15.2-1_debian11_amd64.deb \
    && dpkg -i prince.deb \
    && rm prince.deb \
    && apt-get update && apt-get install -f -y

# Install Python dependencies
COPY config/requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Make scripts executable
RUN chmod +x /app/scripts/docker-entrypoint.sh

# Collect static files (if needed)
# RUN python manage.py collectstatic --noinput

# Expose port (Django default)
EXPOSE 8000

# Start server with entrypoint script
CMD ["/app/scripts/docker-entrypoint.sh"]
