#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Aider API Server with Docker...${NC}"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Create temp directory if it doesn't exist
if [ ! -d "./temp" ]; then
    echo -e "${YELLOW}📁 Creating temp directory...${NC}"
    mkdir -p ./temp
fi

# Build and run with docker-compose
echo -e "${GREEN}🔨 Building and starting containers...${NC}"
docker-compose up --build

echo -e "${GREEN}✅ Aider API Server is running!${NC}"
echo -e "${GREEN}🌐 API Documentation: http://localhost:8000/docs${NC}"
echo -e "${GREEN}🔍 Health Check: http://localhost:8000/health${NC}"
echo -e "${YELLOW}📝 Press Ctrl+C to stop the server${NC}" 