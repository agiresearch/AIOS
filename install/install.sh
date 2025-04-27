#!/bin/bash

# Installation directory
INSTALL_DIR="$HOME/.aios-1"
REPO_URL="https://github.com/agiresearch/AIOS"
BIN_DIR="$HOME/.local/bin"  # User-level bin directory

echo "Installing AIOS..."

# Ensure bin directory exists
mkdir -p "$BIN_DIR"

# Add bin directory to PATH if not already present
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc" 2>/dev/null || true
    export PATH="$HOME/.local/bin:$PATH"
fi

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Clone the repository
git clone "$REPO_URL" "$INSTALL_DIR/src"

# Checkout the specific tag
cd "$INSTALL_DIR/src"

# Find Python executable path
PYTHON_PATH=$(command -v python3)
if [ -z "$PYTHON_PATH" ]; then
    PYTHON_PATH=$(command -v python)
fi

if [ -z "$PYTHON_PATH" ]; then
    echo "Error: Could not find Python executable"
    exit 1
fi

echo "Using Python at: $PYTHON_PATH"

# Check Python version
PYTHON_VERSION=$("$PYTHON_PATH" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ ! "$PYTHON_VERSION" =~ ^3\.(10|11)$ ]]; then
    echo "Error: Unsupported Python version $PYTHON_VERSION. Only Python 3.10 or 3.11 are supported."
    # Clean up the cloned repository since we're aborting
    cd ..
    rm -rf "$INSTALL_DIR"
    exit 1
fi

# Create virtual environment
"$PYTHON_PATH" -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"

# Upgrade pip to latest version
python -m pip install --upgrade pip

pip install -r "$INSTALL_DIR/src/requirements.txt"

# Remove non-kernel files but preserve necessary scripts
mkdir -p "$INSTALL_DIR/src/scripts_temp"
cp "$INSTALL_DIR/src/scripts/list_agents.py" "$INSTALL_DIR/src/scripts_temp/"
rm -rf "$INSTALL_DIR/src/scripts"
mkdir -p "$INSTALL_DIR/src/scripts"
mv "$INSTALL_DIR/src/scripts_temp/list_agents.py" "$INSTALL_DIR/src/scripts/"
rm -rf "$INSTALL_DIR/src/scripts_temp"

rm -rf "$INSTALL_DIR/src/tests"
rm -rf "$INSTALL_DIR/src/docs"

rm "$INSTALL_DIR/src/requirements-cuda.txt"
# rm "$INSTALL_DIR/src/requirements-dev.txt"
# rm "$INSTALL_DIR/src/requirements-research.txt"
# rm "$INSTALL_DIR/src/CONTRIBUTE.md"
rm "$INSTALL_DIR/src/.dockerignore"
rm "$INSTALL_DIR/src/.env.example"
rm "$INSTALL_DIR/src/.precommit-config.yaml"
rm "$INSTALL_DIR/src/README.md"
rm "$INSTALL_DIR/src/Dockerfile"

# Create initial .env if it doesn't exist
touch "$INSTALL_DIR/.env"

# Create executable script
cat > "$BIN_DIR/aios" << 'EOF'
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

    # Check Python version before starting
    PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if [[ ! "$PYTHON_VERSION" =~ ^3\.(10|11)$ ]]; then
        echo "Error: Unsupported Python version $PYTHON_VERSION. Only Python 3.10 or 3.11 are supported."
        return 1
    fi

    load_env
    cd "$INSTALL_DIR/src"
    nohup uvicorn runtime.kernel:app --reload > "$INSTALL_DIR/server.log" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Server started... give it up to 60 seconds to fully initialize!"
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

    # Check Python version before updating
    source "$INSTALL_DIR/venv/bin/activate"
    PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if [[ ! "$PYTHON_VERSION" =~ ^3\.(10|11)$ ]]; then
        echo "Error: Unsupported Python version $PYTHON_VERSION. Only Python 3.10 or 3.11 are supported."
        return 1
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
    pip install -r requirements.txt

    # Remove any new non-kernel files that might have been added
    rm -rf "$INSTALL_DIR/src/scripts"
    rm -rf "$INSTALL_DIR/src/tests"
    rm -rf "$INSTALL_DIR/src/docs"

    rm -f "$INSTALL_DIR/src/requirements-cuda.txt"
    rm -f "$INSTALL_DIR/src/.dockerignore"
    rm -f "$INSTALL_DIR/src/.env.example"
    rm -f "$INSTALL_DIR/src/.precommit-config.yaml"
    rm -f "$INSTALL_DIR/src/README.md"
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

    # Remove the executable
    rm -f "$HOME/.local/bin/aios"

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
        sed -i.bak "/^$varname=/d" "$ENV_FILE" && rm "$ENV_FILE.bak"
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
                sed -i.bak "/^$varname=/d" "$ENV_FILE" && rm "$ENV_FILE.bak"
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
    "refresh")
        if [ -f "$PID_FILE" ]; then
            echo "Refreshing AIOS configuration..."
            # Get server configuration from the configuration file
            HOST=$(python -c "from aios.config.config_manager import config; print(config.config.get('server', {}).get('host', 'localhost'))")
            PORT=$(python -c "from aios.config.config_manager import config; print(config.config.get('server', {}).get('port', 8000))")
            curl -X POST "http://${HOST}:${PORT}/core/refresh"
        else
            echo "Server is not running. Please start the server first."
            echo "Run: aios start"
        fi
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
                cat << 'HELP'
Environment Variable Management

Usage: aios env <subcommand>

Subcommands:
  add     Add a new environment variable
          - Interactive prompt for name and value
          - Values are stored securely in ~/.aios-1/.env
          - Names must be alphanumeric with underscores
          - Values are hidden during input

  list    List all configured environment variables
          - Shows variable names only (values hidden)
          - Useful for checking configured variables

  remove  Remove an environment variable
          - Interactive selection from current variables
          - Immediate removal from configuration

Note: Server restart required for environment changes to take effect
HELP
                ;;
        esac
        ;;
    "agents")
        case "$2" in
            "list")
                # Activate virtual environment and run Python script
                source "$INSTALL_DIR/venv/bin/activate"
                python "$INSTALL_DIR/src/scripts/list_agents.py"
                ;;
            *)
                cat << 'HELP'
Agent Management

Usage: aios agents <subcommand>

Subcommands:
  list    List all available agents
          - Shows Cerebrum built-in agents
          - Shows cached agents from previous installations
          - Shows available agents to install from AIOS foundation
          - Displays versions and sources for each agent

Note: Requires active internet connection for online agent listing
HELP
                ;;
        esac
        ;;
    "clean")
        clean
        ;;
    *)
        cat << 'HELP'
AIOS Command Line Interface

Usage: aios <command> [options]

Commands:
  start         Start the AIOS server
                The server will run in the background and be available at http://localhost:8000
                Logs will be written to ~/.aios-1/server.log

  stop          Stop the running AIOS server
                This will gracefully shutdown any running server instance

  restart       Restart the AIOS server
                Equivalent to running 'stop' followed by 'start'

  update        Update AIOS to the latest version
                - Stops the server if running
                - Pulls latest changes from the repository
                - Updates dependencies
                - Restarts the server automatically
                - Your environment variables and configurations are preserved

  refresh       Refresh AIOS configuration
                - Reloads configuration without restart
                - Server must be running

  env           Manage environment variables
                Subcommands:
                  add     - Add a new environment variable (interactive)
                  list    - List all configured variables (values hidden)
                  remove  - Remove a variable (interactive)
                Environment changes require server restart to take effect

  agents        Manage AIOS agents
                Subcommands:
                  list    - List all available agents
                          • Shows Cerebrum built-in agents
                          • Shows cached agents from previous installations
                          • Shows available agents to install from AIOS foundation
                          • Displays versions and sources for each agent

  clean         Uninstall AIOS completely
                - Stops any running server
                - Removes all AIOS files and configurations
                - Deletes the installation directory
                - Removes the aios command
                Warning: This action cannot be undone!

Examples:
  aios start             # Start the server
  aios env add          # Add a new API key or configuration value
  aios agents list      # View all available agents
  aios update           # Update to the latest version

Notes:
  - Server runs at http://localhost:8000 by default
  - Log file location: ~/.aios-1/server.log
  - Configuration directory: ~/.aios-1
  - Environment file: ~/.aios-1/.env
  - Requires Python 3.10 or 3.11

For more information, visit: https://github.com/agiresearch/AIOS
HELP
        exit 1
        ;;
esac
EOF

# Make it executable
chmod +x "$BIN_DIR/aios"

cat << 'COMPLETE'
🎉 AIOS installed successfully!

The 'aios' command is now available in your terminal.
Installation directory: ~/.aios-1

Quick Start:
1. Add any required environment variables:
   aios env add

2. Start the server:
   aios start

3. Check the server status:
   curl http://localhost:8000/core/status

For a full list of commands and options:
   aios --help

Server logs will be available at:
~/.aios-1/server.log

Note: AIOS requires Python 3.10 or 3.11

For more information, visit:
https://github.com/agiresearch/AIOS
COMPLETE
