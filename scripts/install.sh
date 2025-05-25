#!/bin/bash

# Areeb Model Web Installation Script

echo "Installing Areeb Model Web..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is required but not installed."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p logs
mkdir -p backups

# Set permissions
echo "Setting permissions..."
chmod +x scripts/*.sh

echo "Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit config.yaml to configure your Qwen3 model endpoint"
echo "2. Run: ./scripts/start.sh"
echo "3. Configure Cursor to use: http://your-server-ip:8001/v1" 