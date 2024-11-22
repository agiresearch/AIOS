#!/bin/bash

# Installation directory
INSTALL_DIR="$HOME/.aios"
REPO_URL="https://github.com/agiresearch/AIOS"
BRANCH="v.20"

echo "Installing AIOS..."

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Clone specific branch
git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR/src"

# Create virtual environment
python3 -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"
pip install -r "$INSTALL_DIR/src/requirements.txt"

# Create initial .env if it doesn't exist
touch "$INSTALL_DIR/.env"

# Create executable script
cat > /usr/local/bin/aios << 'EOF'
#!/bin/bash

INSTALL_DIR="$HOME/.aios"
PID_FILE="$INSTALL_DIR/server.pid"
ENV_FILE="$INSTALL_DIR/.env"
ENV_HASH_FILE="$INSTALL_DIR/.env.hash"

# Function to load environment variables
load_env() {
    if [ -f "$ENV_FILE" ]; then
        export $(cat "$ENV_FILE" | xargs)
    fi
}

# Function to check if .env has changed
env_changed() {
    if [ ! -f "$ENV_HASH_FILE" ]; then
        md5 -q "$ENV_FILE" > "$ENV_HASH_FILE"
        return 0
    fi
    
    old_hash=$(cat "$ENV_HASH_FILE")
    new_hash=$(md5 -q "$ENV_FILE")
    
    if [ "$old_hash" != "$new_hash" ]; then
        echo "$new_hash" > "$ENV_HASH_FILE"
        return 0
    fi
    return 1
}

start() {
    if [ -f "$PID_FILE" ]; then
        echo "Server is already running"
        return
    fi
    source "$INSTALL_DIR/venv/bin/activate"
    load_env
    cd "$INSTALL_DIR/src"
    nohup uvicorn server1:app --reload > "$INSTALL_DIR/server.log" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Server started with current environment variables"
}

stop() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        kill $pid
        rm "$PID_FILE"
        echo "Server stopped"
    else
        echo "Server is not running"
    fi
}

restart() {
    stop
    sleep 2
    start
}

watch_env() {
    while true; do
        if env_changed; then
            echo "Environment variables changed, restarting server..."
            restart
        fi
        sleep 5
    done
}

case "$1" in
    "start")
        start
        watch_env &  # Start env watcher in background
        ;;
    "stop")
        stop
        pkill -f "aios.*watch_env"  # Kill env watcher
        ;;
    "restart")
        restart
        ;;
    "env")
        if [ -f "$ENV_FILE" ]; then
            cat "$ENV_FILE"
        else
            echo "No environment variables set"
        fi
        ;;
    *)
        echo "Usage: aios {start|stop|restart|env}"
        exit 1
        ;;
esac
EOF

# Make it executable
sudo chmod +x /usr/local/bin/aios

echo "AIOS installed successfully!"
echo "Use:"
echo "  - 'aios start' to start the server"
echo "  - 'aios stop' to stop the server"
echo "  - 'aios restart' to restart the server"
echo "  - 'aios env' to view current environment variables"
echo ""
echo "To modify environment variables, edit: $INSTALL_DIR/.env"
echo "The server will automatically restart when environment variables change"