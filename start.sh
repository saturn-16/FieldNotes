#!/bin/bash
set -e

echo "=== Starting Field Notes Deployment ==="

# Start Ollama background service
echo "Starting Ollama server..."
ollama serve > /tmp/ollama.log 2>&1 &

# Wait for Ollama to accept connections
echo "Waiting for Ollama to be ready..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama is online!"
        break
    fi
    sleep 1
done

# Ensure model is downloaded
MODEL="${DEFAULT_MODEL:-llama3.2:3b}"
echo "Verifying Ollama model: ${MODEL}..."
ollama pull "${MODEL}" || echo "Warning: model pull failed, checking if already available."

# Start FastAPI application on specified port (default 7860 for Hugging Face)
APP_PORT="${PORT:-7860}"
echo "Starting FastAPI on port ${APP_PORT}..."
exec uvicorn main:app --host 0.0.0.0 --port "${APP_PORT}"
