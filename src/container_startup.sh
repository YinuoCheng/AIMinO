#!/usr/bin/env bash
set -e

echo "Setting up permissions..."
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix

echo "Cleaning up previous X server..."
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99

echo "Starting X server..."
Xvfb :99 -screen 0 1600x900x24 -ac +extension GLX +render -noreset &
sleep 3

echo "Starting window manager..."
fluxbox &
sleep 2

echo "Starting VNC server..."
x11vnc -display :99 -forever -nopw -rfbport 5901 &
sleep 2

echo "Starting noVNC web server..."
websockify --web=/usr/share/novnc 6080 localhost:5901 &
sleep 2


LLM_BACKEND=${LLM_BACKEND:-huggingface}
if [ "$LLM_BACKEND" = "ollama" ]; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 3

    
    echo "Waiting for Ollama to be ready..."
    for i in {1..60}; do
        if curl -sf http://127.0.0.1:11434/api/tags >/dev/null; then
            echo "Ollama is ready"
            break
        fi
        sleep 1
    done

    echo "Pulling model (if not present)..."
    ollama pull llama3.2:3b || true
else
    echo "LLM_BACKEND is $LLM_BACKEND, skipping Ollama startup"
fi

echo "Starting napari LLM application..."
cd /app
if [ -f napariLLM.py ]; then
    python napariLLM.py &
else
    echo "Warning: napariLLM.py not found, starting napari instead"
    napari &
fi

echo "All services started. Access at http://localhost:6080/vnc_auto.html"
wait
