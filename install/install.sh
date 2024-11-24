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

# Remove non-kernel files
rm -rf "$INSTALL_DIR/src/experiment"
rm -rf "$INSTALL_DIR/src/scripts"
rm -rf "$INSTALL_DIR/src/tests"
rm -rf "$INSTALL_DIR/src/aios-figs"

rm "$INSTALL_DIR/src/requirements-cuda.txt"
rm "$INSTALL_DIR/src/requirements-dev.txt"
rm "$INSTALL_DIR/src/requirements-research.txt"
rm "$INSTALL_DIR/src/.dockerignore"
rm "$INSTALL_DIR/src/.env.example"
rm "$INSTALL_DIR/src/.precommit-config.yaml"
rm "$INSTALL_DIR/src/README.md"
rm "$INSTALL_DIR/src/CONTRIBUTE.md"
rm "$INSTALL_DIR/src/Dockerfile"

# Create initial .env if it doesn't exist
touch "$INSTALL_DIR/.env"

# Create executable script
cat > /usr/local/bin/aios << 'EOF'
#!/bin/bash

INSTALL_DIR="$HOME/.aios"
PID_FILE="$INSTALL_DIR/server.pid"
ENV_FILE="$INSTALL_DIR/.env"
ENV_HASH_FILE="$INSTALL_DIR/.env.hash"
WATCHER_PID_FILE="$INSTALL_DIR/watcher.pid"

# Function to load environment variables
load_env() {
    if [ -f "$ENV_FILE" ]; then
        export $(cat "$ENV_FILE" | xargs)
    fi
}

# Function to check if .env has changed
env_changed() {
    if [ ! -f "$ENV_FILE" ]; then
        touch "$ENV_FILE"  # Create empty .env file if it doesn't exist
    fi
    
    if [ ! -f "$ENV_HASH_FILE" ]; then
        md5 "$ENV_FILE" | awk '{print $4}' > "$ENV_HASH_FILE"
        return 0
    fi
    
    old_hash=$(cat "$ENV_HASH_FILE")
    new_hash=$(md5 "$ENV_FILE" | awk '{print $4}')
    
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
    nohup uvicorn runtime.kernel:app --reload > "$INSTALL_DIR/server.log" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Server started with current environment variables"
}

stop() {
    # Stop the server
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        kill $pid 2>/dev/null || true
        rm "$PID_FILE"
        echo "Server stopped"
    else
        echo "Server is not running"
    fi

    # Stop the watcher
    if [ -f "$WATCHER_PID_FILE" ]; then
        watcher_pid=$(cat "$WATCHER_PID_FILE")
        kill $watcher_pid 2>/dev/null || true
        rm "$WATCHER_PID_FILE"
        echo "Environment watcher stopped"
    fi
}

restart() {
    stop
    sleep 2
    start
}

update() {
    echo "Checking for updates..."
    
    # Stop server if running
    if [ -f "$PID_FILE" ]; then
        echo "Stopping server for update..."
        stop
    fi
    
    # Store current commit hash
    cd "$INSTALL_DIR/src"
    current_hash=$(git rev-parse HEAD)
    
    # Fetch and pull latest changes
    git fetch origin
    remote_hash=$(git rev-parse origin/$(git rev-parse --abbrev-ref HEAD))
    
    if [ "$current_hash" = "$remote_hash" ]; then
        echo "Already up to date!"
        start
        return
    fi
    
    echo "Updates found, installing..."
    
    # Pull latest changes
    git pull
    
    # Activate venv and update dependencies
    source "$INSTALL_DIR/venv/bin/activate"
    pip install -r requirements.txt
    
    # Remove any new non-kernel files that might have been added
    rm -rf "$INSTALL_DIR/src/experiment"
    rm -rf "$INSTALL_DIR/src/scripts"
    rm -rf "$INSTALL_DIR/src/tests"
    rm -rf "$INSTALL_DIR/src/aios-figs"
    
    rm -f "$INSTALL_DIR/src/requirements-cuda.txt"
    rm -f "$INSTALL_DIR/src/requirements-dev.txt"
    rm -f "$INSTALL_DIR/src/requirements-research.txt"
    rm -f "$INSTALL_DIR/src/.dockerignore"
    rm -f "$INSTALL_DIR/src/.env.example"
    rm -f "$INSTALL_DIR/src/.precommit-config.yaml"
    rm -f "$INSTALL_DIR/src/README.md"
    rm -f "$INSTALL_DIR/src/CONTRIBUTE.md"
    rm -f "$INSTALL_DIR/src/Dockerfile"
    
    echo "Update complete!"
    
    # Restart server
    start
}

clean() {
    # First stop everything
    stop
    
    # Kill any remaining env watchers (belt and suspenders approach)
    pkill -f "aios.*watch_env" 2>/dev/null || true
    
    # Deactivate virtual environment if active
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate
    fi
    
    # Remove the installation directory
    rm -rf "$INSTALL_DIR"
    echo "AIOS installation cleaned up successfully"
}

watch_env() {
    # Save watcher PID
    echo $$ > "$WATCHER_PID_FILE"
    
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
        ;;
    "restart")
        restart
        ;;
    "update")
        update
        ;;
    "env")
        if [ -f "$ENV_FILE" ]; then
            cat "$ENV_FILE"
        else
            echo "No environment variables set"
        fi
        ;;
    "clean")
        clean
        ;;
    *)
        echo "Usage: aios {start|stop|restart|update|env|clean}"
        exit 1
        ;;
esac
EOF

# Make it executable
chmod +x /usr/local/bin/aios

echo "AIOS installed successfully!"
echo "Use:"
echo "  - 'aios start' to start the server"
echo "  - 'aios stop' to stop the server"
echo "  - 'aios restart' to restart the server"
echo "  - 'aios update' to update to the latest version"
echo "  - 'aios env' to view current environment variables"
echo "  - 'aios clean' to remove AIOS installation"
echo ""
echo "To modify environment variables, edit: $INSTALL_DIR/.env"
echo "The server will automatically restart when environment variables change"