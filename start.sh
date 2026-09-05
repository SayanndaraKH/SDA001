#!/bin/bash
set -e

echo "=================================================="
echo " Starting SYD Downloader Pro on Railway..."
echo "=================================================="

# Start unidbg signature service on port 9099 in background
echo "[*] Starting local unidbg-sign server on port 9099..."
cd /app/app/sign
java -Xmx512m -XX:+ExitOnOutOfMemoryError \
     --add-opens java.base/java.lang=ALL-UNNAMED \
     -cp unidbg-sign.jar com.hongguo.sign.FqTrace serve 9099 &
SIGN_PID=$!
echo "[+] unidbg-sign started (PID: $SIGN_PID)"

cd /app

# Wait up to 15 seconds for signer port 9099 to become responsive
echo "[*] Verifying signer readiness..."
READY=0
for i in $(seq 1 30); do
    if python -c "import socket; s = socket.socket(); s.settimeout(0.5); exit(0 if s.connect_ex(('127.0.0.1', 9099)) == 0 else 1)" 2>/dev/null; then
        echo "[+] Signer is ready and listening on 127.0.0.1:9099!"
        READY=1
        break
    fi
    sleep 0.5
done

if [ $READY -eq 0 ]; then
    echo "[!] Warning: Signer did not respond on 9099 within 15s. Continuing anyway..."
fi

# Railway injects the PORT environment variable
TARGET_PORT="${PORT:-8000}"
export BIND_HOST="0.0.0.0"
export PORT="$TARGET_PORT"
export SIGN_SERVER="http://127.0.0.1:9099"
export HG_LICENSE_DISABLED="1"
export HG_OUT="/app/data/downloads"
export RAILWAY_ENVIRONMENT="1"

mkdir -p /app/data/downloads

echo "[*] Starting FastAPI Web Server on 0.0.0.0:${TARGET_PORT}..."
exec python app/server.py
