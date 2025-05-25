# Areeb Model Web

A comprehensive proxy server that enables Cursor IDE to use self-hosted Qwen3 models with full tool support.

## Features

- Full compatibility with Cursor's tool ecosystem
- File operations (read, write, edit, delete)
- Directory listing and search
- Terminal command execution
- Fuzzy file search
- Grep functionality
- Web search capabilities
- Configurable security settings

## Quick Start

1. Install dependencies:
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

2. Configure your settings in `config.yaml`

3. Start the proxy:
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

4. Configure Cursor to use: `http://198.145.127.150:8001/v1`

## Configuration

Edit `config.yaml` to customize:
- Qwen3 model endpoint
- Security settings
- Tool permissions
- Logging levels

## Security

- File access is restricted to configured directories
- Terminal commands can be filtered
- All operations are logged

## Docker Support

```bash
cd docker
docker-compose up -d
```

## API Endpoints

- `POST /v1/chat/completions` - Chat completions with tool support
- `GET /v1/models` - List available models
- `GET /health` - Health check

## Tool Support

The proxy implements all Cursor tools:
- File operations (read, write, edit, delete)
- Directory listing
- Terminal command execution
- File search (fuzzy and grep)
- Codebase search

## License

MIT License 