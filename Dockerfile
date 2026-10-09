FROM python:3.11-slim

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Install system dependencies: audio codecs, curl, certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    libsndfile1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Configure non-root user (Hugging Face Spaces default UID 1000)
RUN useradd -m -u 1000 user
ENV HOME=/home/user
ENV PATH="/home/user/.local/bin:${PATH}"
ENV OLLAMA_MODELS=/home/user/.ollama/models

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set up permissions and make start script executable
RUN mkdir -p /home/user/.ollama /app/data && \
    chmod +x /app/start.sh && \
    chown -R user:user /app /home/user

# Switch to non-root user
USER user

EXPOSE 7860

CMD ["/app/start.sh"]
