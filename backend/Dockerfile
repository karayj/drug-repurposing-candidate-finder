FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including CA certificates
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy and install RAND PKI certificates
COPY RAND_PKI_Root.pem /usr/local/share/ca-certificates/RAND_PKI_Root.crt
COPY RAND_PKI_Chain.pem /usr/local/share/ca-certificates/RAND_PKI_Chain.crt
RUN update-ca-certificates

# Set certificate environment variables for Python/pip
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Copy requirements
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel certifi && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
