#!/bin/bash

# Areeb Model Web Startup Script

echo "Starting Areeb Model Web..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run ./scripts/install.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if config file exists
if [ ! -f "config.yaml" ]; then
    echo "Warning: config.yaml not found. Using default configuration."
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the server
echo "Starting proxy server..."
python proxy_server.py

# Deactivate virtual environment on exit
deactivate 