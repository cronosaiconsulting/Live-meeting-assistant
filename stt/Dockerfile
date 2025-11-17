# WhisperLive STT Service Dockerfile
# Based on Collabora's WhisperLive project

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install WhisperLive and dependencies
RUN pip install --no-cache-dir \
    whisper-live==0.5.1 \
    faster-whisper==1.0.0 \
    websockets==12.0 \
    numpy==1.24.3

# Create cache directory for models
RUN mkdir -p /root/.cache/whisper

# Expose WebSocket port
EXPOSE 9090

# Environment variables for configuration
ENV MODEL_SIZE=large-v3
ENV LANGUAGE=en
ENV BACKEND=faster_whisper
ENV DEVICE=cpu
ENV COMPUTE_TYPE=int8

# Run WhisperLive server
# Note: This is a placeholder command. In actual deployment,
# you would run the actual WhisperLive server script.
# For now, this creates a basic structure.

CMD echo "WhisperLive STT Service" && \
    echo "Model: $MODEL_SIZE" && \
    echo "Language: $LANGUAGE" && \
    echo "Device: $DEVICE" && \
    echo "Starting server on port 9090..." && \
    python -c "import websockets; import asyncio; print('STT service placeholder - implement WhisperLive server')" && \
    tail -f /dev/null

# TODO: Replace with actual WhisperLive server command:
# CMD ["python", "-m", "whisper_live.server", "--port", "9090", "--model", "${MODEL_SIZE}"]
