# --- dmarket_bot Setup Script for Windows 11 (PowerShell) ---

# Repository URL
$RepoUrl = "https://github.com/Cfomodz/dmarket_bot.git"
$ProjectDir = "dmarket_bot" # The directory name where the repo will be cloned

Write-Host "🚀 Starting dmarket_bot setup for Windows..."

# --- Helper function for error handling ---
function Handle-Error {
    param(
        [string]$ErrorMessage
    )
    Write-Error "❌ ERROR: $ErrorMessage"
    Write-Host "Aborting setup."
    # Pause to allow user to see the error before exiting in some environments
    Read-Host -Prompt "Press Enter to exit"
    exit 1
}

# 1. Clone repository
if (Test-Path $ProjectDir) {
    Write-Host "⚠️ Directory '$ProjectDir' already exists. Attempting to pull latest changes."
    try {
        Set-Location $ProjectDir -ErrorAction Stop
        git pull
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not pull latest changes. Continuing with existing version."
        }
    } catch {
        Handle-Error "Failed to enter existing $ProjectDir directory: $($_.Exception.Message)"
    }
} else {
    Write-Host "Cloning repository: $RepoUrl into '$ProjectDir' directory..."
    try {
        git clone $RepoUrl $ProjectDir -ErrorAction Stop
        Set-Location $ProjectDir -ErrorAction Stop
    } catch {
        Handle-Error "Git clone failed. Check the REPO_URL and your internet connection. Error: $($_.Exception.Message)"
    }
}
Write-Host "✅ Repository ready."

# 2. Create Python virtual environment
Write-Host "🐍 Creating Python virtual environment (venv)..."
try {
    # Try 'python' first, then 'python3' if 'python' is not found or fails
    python -m venv venv -ErrorAction Stop
} catch {
    try {
        Write-Warning "Command 'python -m venv venv' failed. Trying 'python3 -m venv venv'..."
        python3 -m venv venv -ErrorAction Stop
    } catch {
         Handle-Error "Failed to create virtual environment. Ensure Python 3 is installed and in PATH. Error: $($_.Exception.Message)"
    }
}
Write-Host "✅ Virtual environment created."

# 3. Activate virtual environment
Write-Host "Activating virtual environment..."
try {
    # Check if execution policy needs adjustment
    $CurrentPolicy = Get-ExecutionPolicy -Scope CurrentUser
    if ($CurrentPolicy -ne "RemoteSigned" -and $CurrentPolicy -ne "Unrestricted") {
        Write-Warning "Your PowerShell execution policy for CurrentUser is '$CurrentPolicy'."
        Write-Warning "The script will attempt to run '.\venv\Scripts\Activate.ps1'."
        Write-Warning "If activation fails, you might need to manually run in your PowerShell window:"
        Write-Warning "Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
        Write-Warning "Then re-run this setup script or manually activate using: .\venv\Scripts\Activate.ps1"
    }
    # Attempt to activate
    .\venv\Scripts\Activate.ps1 -ErrorAction SilentlyContinue # Try to activate, but don't stop script if it fails due to policy
    
    # Check if venv is active by looking for a common venv indicator in the prompt or environment
    # This is a basic check; more robust checks might be needed depending on PS customization
    if ($env:VIRTUAL_ENV) {
        Write-Host "✅ Virtual environment activated."
    } else {
        Write-Warning "⚠️ Virtual environment might not be active. This could be due to PowerShell execution policy."
        Write-Warning "Please ensure it's active before running the bot. You can try running '.\venv\Scripts\Activate.ps1' manually."
        Write-Warning "If that fails, run: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
        Write-Warning "Then try activating again: .\venv\Scripts\Activate.ps1"
    }

} catch {
    # This catch block might not be hit if -ErrorAction SilentlyContinue is used above
    Handle-Error "Failed to activate virtual environment. Ensure PowerShell execution policy allows script execution (e.g., 'Set-ExecutionPolicy RemoteSigned -Scope CurrentUser'). Error: $($_.Exception.Message)"
}


# 4. Install requirements
if (Test-Path "requirements.txt") {
    Write-Host "📦 Installing dependencies from requirements.txt..."
    try {
        pip install -r requirements.txt -ErrorAction Stop
        Write-Host "✅ Dependencies installed."
    } catch {
        Handle-Error "Failed to install requirements. Check requirements.txt, your internet connection, and ensure the virtual environment is active. Error: $($_.Exception.Message)"
    }
} else {
    Write-Warning "⚠️ requirements.txt not found. Skipping dependency installation. Please ensure this file exists in your repository."
}

# 5. Create template credentials.py
Write-Host "🔑 Creating template credentials.py file..."
$CredentialContent = @"
# DMarket API Credentials
# IMPORTANT: Replace the placeholder values below with your actual DMarket API keys.

PUBLIC_KEY = "YOUR_PUBLIC_API_KEY_HERE"
SECRET_KEY = "YOUR_SECRET_API_KEY_HERE"
"@

try {
    Set-Content -Path "credentials.py" -Value $CredentialContent -Encoding UTF8 -ErrorAction Stop
    Write-Host "✅ Template credentials.py created successfully."
} catch {
    Handle-Error "Failed to create template credentials.py. Error: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "🎉 Setup complete for dmarket_bot! 🎉"
Write-Host ""
Write-Host "👉 IMPORTANT NEXT STEP: 👈"
Write-Host "You MUST edit the 'credentials.py' file located in the '$ProjectDir' directory."
Write-Host "Open it with a text editor (like Notepad or VS Code) and replace 'YOUR_PUBLIC_API_KEY_HERE' and 'YOUR_SECRET_API_KEY_HERE' with your actual DMarket API keys."
Write-Host ""
Write-Host "To run your bot (after editing credentials.py):"
Write-Host "1. Ensure you are in the '$ProjectDir' directory: cd \path\to\$ProjectDir (if not already there)"
Write-Host "2. Activate the virtual environment (if you open a new PowerShell window or next time you want to run it): .\venv\Scripts\Activate.ps1"
Write-Host "3. Execute your main bot script (e.g., python main.py)"
Write-Host ""
Write-Host "Remember to replace 'your_main_bot_script.py' with the actual name of your bot's main Python file."
Write-Host "If you had to change your ExecutionPolicy, you might consider changing it back for security reasons after you are done, though 'RemoteSigned' is generally safe for user-specific scripts."
# Add a final pause for the user to read the output, especially if run by double-clicking
Read-Host -Prompt "Press Enter to close this window"
