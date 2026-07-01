#!/bin/bash

echo "🔐 Setting up RAND SSL Certificates..."
echo ""

CERT_SOURCE="/Users/Shared/RANDCerts"
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"

# Check if RAND certificates exist
if [ ! -d "$CERT_SOURCE" ]; then
    echo "⚠️  Warning: RAND certificates not found at $CERT_SOURCE"
    echo "This is only required if you're on the RAND corporate network."
    echo ""
    exit 0
fi

# Copy certificates to backend
echo "📋 Copying certificates to backend..."
cp "$CERT_SOURCE/RAND_PKI_Root.pem" "$BACKEND_DIR/"
cp "$CERT_SOURCE/RAND_PKI_Chain.pem" "$BACKEND_DIR/"

# Copy certificates to frontend
echo "📋 Copying certificates to frontend..."
cp "$CERT_SOURCE/RAND_PKI_Root.pem" "$FRONTEND_DIR/"
cp "$CERT_SOURCE/RAND_PKI_Chain.pem" "$FRONTEND_DIR/"

echo ""
echo "✅ RAND SSL certificates copied successfully!"
echo ""
echo "You can now run: docker-compose up --build"
