#!/bin/bash

echo "🚀 Starting Drug Repurposing Candidate Finder..."
echo ""

# Check and setup RAND certificates
if [ ! -f backend/RAND_PKI_Root.pem ] || [ ! -f frontend/RAND_PKI_Root.pem ]; then
    echo "🔐 RAND SSL certificates not found. Setting up..."
    ./setup-rand-certs.sh
    echo ""
fi

# Check if .env exists, if not create from example
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
fi

# Start Docker Compose
echo "🐳 Starting Docker containers..."
echo "This may take a few minutes on first run..."
echo ""
docker-compose up --build

echo ""
echo "✅ Application started successfully!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "📡 Backend API: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
