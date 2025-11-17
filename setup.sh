#!/bin/bash

# AI-Enhanced Video Meeting PoC - Quick Setup Script
# This script automates the initial deployment process

set -e  # Exit on error

echo "🚀 AI-Enhanced Video Meeting PoC - Quick Setup"
echo "==============================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env

    echo ""
    echo "🔐 Generating secrets..."

    # Generate secrets
    JWT_SECRET=$(openssl rand -hex 32)
    LIVEKIT_API_KEY="LK$(openssl rand -hex 16)"
    LIVEKIT_API_SECRET=$(openssl rand -base64 48)
    POSTGRES_PASSWORD=$(openssl rand -base64 24)

    # Update .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env
        sed -i '' "s/LIVEKIT_API_KEY=.*/LIVEKIT_API_KEY=$LIVEKIT_API_KEY/" .env
        sed -i '' "s/LIVEKIT_API_SECRET=.*/LIVEKIT_API_SECRET=$LIVEKIT_API_SECRET/" .env
        sed -i '' "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env
    else
        # Linux
        sed -i "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env
        sed -i "s/LIVEKIT_API_KEY=.*/LIVEKIT_API_KEY=$LIVEKIT_API_KEY/" .env
        sed -i "s/LIVEKIT_API_SECRET=.*/LIVEKIT_API_SECRET=$LIVEKIT_API_SECRET/" .env
        sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env
    fi

    echo "✅ Secrets generated and saved to .env"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your KIMI K2 API key:"
    echo "   LLM_API_KEY=sk-your-kimi-k2-api-key"
    echo ""
    echo "Also consider changing the default admin password:"
    echo "   ADMIN_DEFAULT_PASSWORD=your-strong-password"
    echo ""
    read -p "Press Enter when you've updated .env, or Ctrl+C to exit..."
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🐳 Starting PostgreSQL database..."
docker compose up -d postgres

echo "⏳ Waiting for database to be ready..."
sleep 10

echo ""
echo "🗄️  Running database migrations..."
docker compose run --rm backend alembic upgrade head

echo ""
echo "🌱 Seeding database with default users..."
docker compose run --rm backend python infra/scripts/seed_db.py

echo ""
echo "🚀 Starting all services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 5

echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📱 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔑 Default Login Credentials:"
echo "   Admin: admin / <your ADMIN_DEFAULT_PASSWORD>"
echo "   User 1: john / user123"
echo "   User 2: jane / user123"
echo ""
echo "📝 To view logs: docker compose logs -f"
echo "🛑 To stop: docker compose down"
echo ""
echo "📚 For more details, see DEPLOYMENT.md"
echo ""
