# Windows PowerShell installation script for AIOS

Write-Host "Cloning the AIOS repository..."
git clone https://github.com/agiresearch/AIOS.git
Set-Location -Path "AIOS"

Write-Host "Creating a virtual environment..."
python -m venv venv
.\venv\Scripts\Activate

Write-Host "Setting up API keys..."

$CONFIG_FILE = ".env"
if (-Not (Test-Path $CONFIG_FILE)) {
    New-Item -ItemType File -Path $CONFIG_FILE
}

function Save-ApiKey {
    param (
        [string]$key_name,
        [string]$user_input
    )
    
    if ($user_input) {
        Add-Content -Path $CONFIG_FILE -Value "$key_name=$user_input"
        Write-Host "$key_name has been saved."
    } else {
        Write-Host "$key_name was skipped."
    }
}

$OPENAI_API_KEY = Read-Host "Enter your OPENAI API key for using OpenAI models (or press Enter to skip)"
Save-ApiKey "OPENAI_API_KEY" $OPENAI_API_KEY

$GEMINI_API_KEY = Read-Host "Enter your GEMINI API key for using OpenAI models (or press Enter to skip)"
Save-ApiKey "GEMINI_API_KEY" $GEMINI_API_KEY

$HF_AUTH_TOKENS = Read-Host "Enter your Huggingface token for using open-sourced models (or press Enter to skip)"
Save-ApiKey "HF_AUTH_TOKENS" $HF_AUTH_TOKENS

$HF_HOME = Read-Host "Enter the directory you would like to store Huggingface models"
Save-ApiKey "HF_HOME" $HF_HOME

# Prompt for GPU environment
$gpu_choice = Read-Host "Do you have a GPU environment for running the models? (Yes/No)"

if ($gpu_choice -eq "Yes") {
    Write-Host "Installing dependencies from requirements-cuda.txt for GPU environment..."
    pip install -r requirements-cuda.txt
} elseif ($gpu_choice -eq "No") {
    Write-Host "Installing dependencies from requirements.txt for CPU environment..."
    pip install -r requirements.txt
} else {
    Write-Host "Invalid choice. Please run the script again and choose Yes or No."
    exit
}

Write-Host "Installation complete. Your API keys are saved in $CONFIG_FILE where you can also update the API keys later."

Write-Host "You need to then customize your aios_config.json to set up configurations. After that, you can run launch.py to start your AIOS web UI locally."
