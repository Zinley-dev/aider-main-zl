#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔨 Building Aider API Server Docker Image...${NC}"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Build the image
echo -e "${BLUE}📦 Building Docker image...${NC}"
docker build -t ghcr.io/zinley-dev/aider-main-zl:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully!${NC}"
    echo -e "${GREEN}🏷️  Image: ghcr.io/zinley-dev/aider-main-zl:latest${NC}"
    
    # Show image info
    echo -e "${BLUE}📋 Image Information:${NC}"
    docker images ghcr.io/zinley-dev/aider-main-zl:latest
    
    echo -e "${YELLOW}🚀 You can now run the container with:${NC}"
    echo -e "${YELLOW}   ./run.sh${NC}"
    echo -e "${YELLOW}   or${NC}"
    echo -e "${YELLOW}   docker-compose up${NC}"
else
    echo -e "${RED}❌ Docker build failed!${NC}"
    exit 1
fi 