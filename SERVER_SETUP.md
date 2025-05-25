# Server Setup Instructions for Areeb Model Web

## Prerequisites
- Your Qwen3 vLLM server should already be running on port 8000
- Python 3.8+ installed on the server
- SSH access to your server (198.145.127.150)

## Step 1: Transfer Project to Server

### Option A: Using Git (Recommended)
```bash
# On your local machine, push to git first
cd areeb-model-web
git init
git add .
git commit -m "Initial commit of areeb-model-web"
git remote add origin <your-repo-url>
git push -u origin main

# Then on your server:
git clone <your-repo-url>
cd areeb-model-web
```

### Option B: Using SCP
```bash
# From your local machine
scp -r areeb-model-web/ user@198.145.127.150:~/
```

## Step 2: Configure on Server

### 1. SSH to your server
```bash
ssh user@198.145.127.150
cd areeb-model-web
```

### 2. Edit configuration
```bash
nano config.yaml
```

**Important settings to update:**
```yaml
model:
  endpoint: "http://127.0.0.1:8000"  # Your Qwen3 vLLM server
  api_key: "sk-your-actual-api-key-here"  # Set your API key
  
security:
  allowed_directories:
    - "/home"
    - "/tmp"
    - "/var/tmp"
    - "/path/to/your/projects"  # Add your project directories
```

### 3. Install dependencies
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

### 4. Start the proxy server
```bash
./scripts/start.sh
```

The server will start on port 8001 and show colored logs.

## Step 3: Test the Setup

### Test health endpoint
```bash
curl http://localhost:8001/health
```

Should return:
```json
{"status": "healthy", "service": "areeb-model-web"}
```

### Test model endpoint
```bash
curl http://localhost:8001/v1/models \
  -H "Authorization: Bearer sk-your-actual-api-key-here"
```

### Test chat completion with tools
```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-actual-api-key-here" \
  -d '{
    "model": "Qwen3-30B-A3B-GPTQ-Int4",
    "messages": [{"role": "user", "content": "List the files in the current directory"}],
    "max_tokens": 1000
  }'
```

## Step 4: Configure Cursor

In Cursor IDE:
1. Go to Settings → Models
2. Add Custom Model:
   - **API Base URL**: `http://198.145.127.150:8001/v1`
   - **API Key**: `sk-your-actual-api-key-here`
   - **Model Name**: `gpt-4` (use this name so Cursor recognizes tool support)

## Step 5: Run as Service (Optional)

To run the proxy as a system service:

### Create systemd service
```bash
sudo nano /etc/systemd/system/areeb-model-web.service
```

```ini
[Unit]
Description=Areeb Model Web Proxy
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/areeb-model-web
ExecStart=/home/your-username/areeb-model-web/venv/bin/python proxy_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and start service
```bash
sudo systemctl daemon-reload
sudo systemctl enable areeb-model-web
sudo systemctl start areeb-model-web
sudo systemctl status areeb-model-web
```

## Troubleshooting

### Check logs
```bash
tail -f logs/areeb-model-web.log
```

### Check if Qwen3 server is running
```bash
curl http://localhost:8000/v1/models
```

### Check proxy server status
```bash
netstat -tlnp | grep 8001
```

### Restart proxy
```bash
./scripts/start.sh
```

## Security Notes

1. **Firewall**: Make sure port 8001 is accessible from your client machine
2. **API Key**: Use a strong, unique API key
3. **Directories**: Only allow access to directories you trust
4. **Commands**: Review allowed commands in config.yaml

## Docker Alternative

If you prefer Docker:
```bash
cd docker
docker-compose up -d
```

This will run the proxy in a container with automatic restarts. 