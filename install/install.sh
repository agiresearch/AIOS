#!/bin/bash

# Installation directory
INSTALL_DIR="$HOME/.aios-1"
REPO_URL="https://github.com/agiresearch/AIOS"
TAG="v0.2.0.beta"  # Replace with your specific tag

echo "Installing AIOS..."

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Clone the repository
git clone "$REPO_URL" "$INSTALL_DIR/src"

# Checkout the specific tag
cd "$INSTALL_DIR/src"
git checkout tags/"$TAG" -b "$TAG-branch"

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

INSTALL_DIR="$HOME/.aios-1"
PID_FILE="$INSTALL_DIR/server.pid"
ENV_FILE="$INSTALL_DIR/.env"

# Function to load environment variables
load_env() {
    if [ -f "$ENV_FILE" ]; then
        export $(cat "$ENV_FILE" | xargs)
    fi
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
    echo "Server started"
}

stop() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        kill $pid 2>/dev/null || true
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
    
    # Deactivate virtual environment if active
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate
    fi
    
    # Remove the installation directory
    rm -rf "$INSTALL_DIR"
    echo "AIOS installation cleaned up successfully"
}

env_add() {
    echo "Adding new environment variable"
    echo "Enter variable name (e.g., API_KEY):"
    read varname
    
    # Validate variable name
    if [[ ! $varname =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
        echo "Invalid variable name. Use only letters, numbers, and underscores, and start with a letter or underscore."
        return 1
    fi
    
    echo "Enter variable value:"
    read -s varvalue  # -s flag hides the input (good for sensitive values)
    echo  # Add newline after hidden input
    
    # Check if variable already exists
    if grep -q "^$varname=" "$ENV_FILE" 2>/dev/null; then
        echo "Variable $varname already exists. Do you want to update it? (y/n)"
        read answer
        if [ "$answer" != "y" ]; then
            echo "Operation cancelled"
            return
        fi
        # Remove old value
        sed -i '' "/^$varname=/d" "$ENV_FILE"
    fi
    
    # Add new value
    echo "$varname=$varvalue" >> "$ENV_FILE"
    echo "Environment variable added successfully"
    echo "Remember to restart the server for changes to take effect"
}

env_list() {
    echo "Current environment variables:"
    if [ -f "$ENV_FILE" ] && [ -s "$ENV_FILE" ]; then
        cat "$ENV_FILE" | sed 's/=.*$/=****/'  # Show variable names but hide values
    else
        echo "No environment variables set"
    fi
}

env_remove() {
    echo "Current environment variables:"
    if [ -f "$ENV_FILE" ] && [ -s "$ENV_FILE" ]; then
        cat "$ENV_FILE" | sed 's/=.*$/=****/' | nl  # Show numbered list
        echo ""
        echo "Enter the number of the variable to remove:"
        read varnum
        
        if [[ "$varnum" =~ ^[0-9]+$ ]]; then
            varname=$(sed -n "${varnum}p" "$ENV_FILE" | cut -d= -f1)
            if [ -n "$varname" ]; then
                sed -i '' "/^$varname=/d" "$ENV_FILE"
                echo "Removed $varname"
                echo "Remember to restart the server for changes to take effect"
            else
                echo "Invalid number"
            fi
        else
            echo "Invalid input"
        fi
    else
        echo "No environment variables set"
    fi
}

case "$1" in
    "start")
        start
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
        case "$2" in
            "add")
                env_add
                ;;
            "list")
                env_list
                ;;
            "remove")
                env_remove
                ;;
            *)
                echo "Usage: aios env {add|list|remove}"
                ;;
        esac
        ;;
    "clean")
        clean
        ;;
    *)
        echo "Usage: aios {start|stop|restart|update|env|clean}"
        echo "For environment variables: aios env {add|list|remove}"
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
echo "  - 'aios env add' to add new environment variables"
echo "  - 'aios env list' to view current environment variables"
echo "  - 'aios env remove' to remove environment variables"
echo "  - 'aios clean' to remove AIOS installation"