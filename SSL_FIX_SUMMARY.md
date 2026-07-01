# SSL Certificate Fix Summary

## Problem
Docker builds were failing with SSL certificate verification errors due to RAND's corporate SSL infrastructure using self-signed certificates.

## Solution
Injected RAND PKI certificates into both backend and frontend Docker images.

## Files Modified

### 1. Backend Dockerfile (`backend/Dockerfile`)
- Added RAND_PKI_Root.pem and RAND_PKI_Chain.pem to system CA certificates
- Set environment variables: `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, `CURL_CA_BUNDLE`
- Updated to use `certifi` for Python SSL verification

### 2. Frontend Dockerfile (`frontend/Dockerfile`)
- Manually appended RAND certificates to Alpine's existing CA bundle
- Set environment variables: `NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE`, `npm_config_cafile`
- Upgraded to Node 20 for better security
- Changed from `npm ci` to `npm install --legacy-peer-deps` (no package-lock.json)

### 3. Certificate Setup Script (`setup-rand-certs.sh`)
- Automated copying of certificates from `/Users/Shared/RANDCerts/` to both backend and frontend directories
- Makes setup process one command

### 4. .gitignore
- Added certificate file patterns to prevent accidental commits

### 5. README.md
- Added step for copying RAND certificates before building

## Required Files

The following certificate files must be in both `backend/` and `frontend/` directories:
- `RAND_PKI_Root.pem`
- `RAND_PKI_Chain.pem`

## Quick Start (RAND Users)

```bash
# 1. Copy certificates to project
./setup-rand-certs.sh

# 2. Build and start all services
docker-compose up --build
```

## Why This Works

### Backend (Python/Debian)
- Debian's `update-ca-certificates` command scans `/usr/local/share/ca-certificates/` for `.crt` files
- We copy `.pem` files as `.crt` (same format, different extension)
- Python's `requests`, `httpx`, and `pip` all respect the system CA bundle

### Frontend (Node/Alpine)
- Alpine Linux already has a CA bundle at `/etc/ssl/certs/ca-certificates.crt`
- We append RAND certificates to this existing file
- Node.js reads this via `NODE_EXTRA_CA_CERTS` environment variable
- npm reads this via `npm_config_cafile` environment variable

## Testing

Both services now build successfully:

```bash
# Test backend build
docker-compose build backend

# Test frontend build  
docker-compose build frontend

# Test full stack
docker-compose up --build
```

## Troubleshooting

### If you see "certificate verify failed" errors:

1. Verify certificates exist:
   ```bash
   ls -la backend/*.pem
   ls -la frontend/*.pem
   ```

2. Re-run certificate setup:
   ```bash
   ./setup-rand-certs.sh
   ```

3. Rebuild with no cache:
   ```bash
   docker-compose build --no-cache
   ```

### If certificates are outdated:

Copy fresh certificates from `/Users/Shared/RANDCerts/`:
```bash
cp /Users/Shared/RANDCerts/RAND_PKI_*.pem backend/
cp /Users/Shared/RANDCerts/RAND_PKI_*.pem frontend/
```

## Security Note

Certificate files (*.pem, *.crt, *.der, *.p7b) are excluded from git via `.gitignore` to prevent accidental commits of sensitive material.
