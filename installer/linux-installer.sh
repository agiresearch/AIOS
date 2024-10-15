#!/bin/bash

# 1. Clone the GitHub repository
echo "Cloning the AIOS..."
git clone https://github.com/agiresearch/AIOS.git
cd repository || exit

# 2. Create a new environment and install dependencies
echo "Creating a virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

# 3. Set up API keys interactively
echo "Setting up API keys..."

# Check if the config file exists; if not, create one
CONFIG_FILE=".env"
if [ ! -f "$CONFIG_FILE" ]; then
    touch "$CONFIG_FILE"
fi

# Ask the user for API keys interactively and store them
save_api_key() {
    local key_name="$1"
    local user_input="$2"
    
    if [ -n "$user_input" ]; then
        echo "$key_name=$user_input" >> "$CONFIG_FILE"
        echo "$key_name has been saved."
    else
        echo "$key_name was skipped."
    fi
}

# Ask the user for API keys interactively and allow pressing Enter to skip
read -p "Enter your OPENAI API key for using openai models (or press Enter to skip): " OPENAI_API_KEY
save_api_key "OPENAI_API_KEY" "$OPENAI_API_KEY"

read -p "Enter your Huggingface token for using open-sourced models (or press Enter to skip): " HF_AUTH_TOKENS
save_api_key "HF_AUTH_TOKENS" "$HF_AUTH_TOKENS"

# Notify the user where keys are stored
echo "Installation complete. Your API keys are saved in $CONFIG_FILE if provided."

# 4. Exit the script, leaving the environment active
echo "Activate your environment with: source venv/bin/activate"
Explanation of Changes:
Function to Save API Keys: The save_api_key function is used to store API keys only if the user enters a value. If the input is empty (i.e., the user pressed "Enter"), the key is skipped.

bash
复制代码
save_api_key() {
    local key_name="$1"
    local user_input="$2"
    
    if [ -n "$user_input" ]; then
        echo "$key_name=$user_input" >> "$CONFIG_FILE"
        echo "$key_name has been saved."
    else
        echo "$key_name was skipped."
    fi
}