#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${BLUE}${BOLD}=====================================${RESET}"
echo -e "${GREEN}${BOLD}    Welcome to AIOS Installation!     ${RESET}"
echo -e "${BLUE}${BOLD}=====================================${RESET}"
echo ""

echo "Cloning the AIOS..."
git clone https://github.com/agiresearch/AIOS.git
cd AIOS || exit

echo "Creating a virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Setting up API keys..."

CONFIG_FILE=".env"
if [ ! -f "$CONFIG_FILE" ]; then
    touch "$CONFIG_FILE"
fi

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

echo -e "${BOLD}Please enter your API keys:${RESET}"

read -p "Enter your OPENAI API key for using OpenAI models (or press Enter to skip): " OPENAI_API_KEY
save_api_key "OPENAI_API_KEY" "$OPENAI_API_KEY"

read -p "Enter your GEMINI API key for using GEMINI models (or press Enter to skip): " GEMINI_API_KEY
save_api_key "GEMINI_API_KEY" "$GEMINI_API_KEY"

read -p "Enter your Huggingface token for using open-sourced models (or press Enter to skip): " HF_AUTH_TOKENS
save_api_key "HF_AUTH_TOKENS" "$HF_AUTH_TOKENS"

read -p "Enter the directory you would like to store Huggingface models: " HF_HOME
save_api_key "HF_HOME" "$HF_HOME"

echo -e "${BOLD}Do you have a GPU environment for running the models?${RESET}"
select gpu_choice in "Yes" "No"; do
    case $gpu_choice in
        Yes )
            echo "Installing dependencies from requirements-cuda.txt for GPU environment..."
            pip install -r requirements-cuda.txt
            break
            ;;
        No )
            echo "Installing dependencies from requirements.txt for CPU environment..."
            pip install -r requirements.txt
            break
            ;;
        * ) echo "Please answer Yes or No.";;
    esac
done

# Final styled message
echo -e "${GREEN}${BOLD}============================================================${RESET}"
echo -e "${GREEN}${BOLD}Installation complete! Your API keys are saved in $CONFIG_FILE.${RESET}"
echo -e "${GREEN}${BOLD}You can also update the API keys later.${RESET}"
echo -e "${GREEN}${BOLD}Next steps: customize your aios_config.json and run launch.py.${RESET}"
echo -e "${GREEN}${BOLD}============================================================${RESET}"
