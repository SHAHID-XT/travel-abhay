FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

# Set work directory
WORKDIR /app

# Install dependencies for GeoDjango
RUN apt-get update && apt-get install -y \
    binutils \
    libproj-dev \
    gdal-bin \
    postgresql-client \
    gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Set permissions
RUN chmod +x /app/entrypoint.sh

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]