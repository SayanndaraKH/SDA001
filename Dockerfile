FROM python:3.11-slim

# Prevent python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    BIND_HOST=0.0.0.0 \
    PORT=8000 \
    SIGN_SERVER=http://127.0.0.1:9099 \
    HG_LICENSE_DISABLED=1

# Install system dependencies:
# - default-jre-headless: required for unidbg-sign.jar (Android ARM/x86 native library simulation)
# - ffmpeg: required for video remuxing and PyAV
# - curl: for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure download and state directories exist with write permissions
RUN mkdir -p /app/app/downloads /app/data /app/data/downloads /app/.stream_cache && \
    chmod +x /app/start.sh

EXPOSE 8000

CMD ["/bin/bash", "/app/start.sh"]
