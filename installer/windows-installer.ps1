$RED = "Red"
$GREEN = "Green"
$BLUE = "Blue"
$BOLD = ""  # No direct bold support, but we'll emphasize via structure
$RESET = "" # No need for reset

# Welcome message with colors
Write-Host "=====================================" -ForegroundColor $BLUE
Write-Host "    Welcome to AIOS Installation!    " -ForegroundColor $GREEN
Write-Host "=====================================" -ForegroundColor $BLUE
Write-Host ""

# Cloning the AIOS repository
Write-Host "Cloning the AIOS..."
git clone https://github.com/agiresearch/AIOS.git
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to clone the AIOS repository." -ForegroundColor $RED
    exit 1
}
Set-Location "AIOS"

# Creating a virtual environment
Write-Host "Creating a virtual environment..."
python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to create virtual environment." -ForegroundColor $RED
    exit 1
}

# Activating the virtual environment
& "venv\Scripts\Activate.ps1"

# Setting up API keys
Write-Host "Setting up API keys..."

$CONFIG_FILE = ".env"
if (-Not (Test-Path $CONFIG_FILE)) {
    New-Item -ItemType File -Path $CONFIG_FILE
}

# Function to save API keys
function Save-APIKey {
    param (
        [string]$key_name,
        [string]$user_input
    )
    if ($user_input -ne "") {
        Add-Content -Path $CONFIG_FILE -Value "$key_name=$user_input"
        Write-Host "$key_name has been saved."
    }
    else {
        Write-Host "$key_name was skipped."
    }
}

# Prompt for API keys
Write-Host "Please enter your API keys:"

$OPENAI_API_KEY = Read-Host "Enter your OPENAI API key for using OpenAI models (or press Enter to skip)"
Save-APIKey -key_name "OPENAI_API_KEY" -user_input $OPENAI_API_KEY

$GEMINI_API_KEY = Read-Host "Enter your GEMINI API key for using GEMINI models (or press Enter to skip)"
Save-APIKey -key_name "GEMINI_API_KEY" -user_input $GEM
