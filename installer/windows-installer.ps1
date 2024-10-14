Write-Host "Cloning the AIOS..."
git clone https://github.com/agiresearch/AIOS.git
Set-Location AIOS

Write-Host "Creating a virtual environment..."
python -m venv venv
.\venv\Scripts\Activate

Write-Host "Installing dependencies..."
pip install -r requirements.txt

Write-Host "Setting up API keys..."

$CONFIG_FILE = ".env"
if (-Not (Test-Path $CONFIG_FILE)) {
    New-Item -Path $CONFIG_FILE -ItemType File
}

function Save-ApiKey {
    param(
        [string]$KeyName,
        [string]$UserInput
    )

    if ($UserInput) {
        Add-Content -Path $CONFIG_FILE -Value "$KeyName=$UserInput"
        Write-Host "$KeyName has been saved."
    } else {
        Write-Host "$KeyName was skipped."
    }
}

$OPENAI_API_KEY = Read-Host "Enter your OPENAI API key for using OpenAI models (or press Enter to skip)"
Save-ApiKey "OPENAI_API_KEY" $OPENAI_API_KEY

$GEMINI_API_KEY = Read-Host "Enter your GEMINI API key for using Gemini models (or press Enter to skip)"
Save-ApiKey "GEMINI_API_KEY" $GEMINI_API_KEY

$HF_AUTH_TOKENS = Read-Host "Enter your Huggingface token for using open-sourced models (or press Enter to skip)"
Save-ApiKey "HF_AUTH_TOKENS" $HF_AUTH_TOKENS

$HF_HOME = Read-Host "Enter the directory you would like to store Huggingface models"
Save-ApiKey "HF_HOME" $HF_HOME

Write-Host "Installation complete. Your API keys are saved in $CONFIG_FILE where you can also update the API keys later."

Write-Host "You need to then customize your aios_config.json to set up configurations. After that, you can run launch.py to start your AIOS web UI locally."
