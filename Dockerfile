FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy application
COPY . .

# Run migrations
RUN python manage.py migrate || true

# Expose port
EXPOSE 8000

# Start command
CMD ["gunicorn", "horilla.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
