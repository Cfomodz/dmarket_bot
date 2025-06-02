#!/bin/bash
# --- dmarket_bot Setup Script for macOS/Linux ---

# Repository URL
REPO_URL="https://github.com/Cfomodz/dmarket_bot.git"
PROJECT_DIR="dmarket_bot"

echo "🚀 Starting dmarket_bot setup for macOS/Linux..."

# --- Helper function for error handling ---
handle_error() {
    echo "❌ ERROR: $1"
    echo "Aborting setup."
    exit 1
}

# 1. Clone repository
if [ -d "$PROJECT_DIR" ]; then
  echo "⚠️ Directory '$PROJECT_DIR' already exists. Attempting to pull latest changes."
  cd "$PROJECT_DIR" || handle_error "Failed to enter existing $PROJECT_DIR directory."
  git pull || echo "⚠️  Could not pull latest changes. Continuing with existing version."
else
  echo "Cloning repository: $REPO_URL into '$PROJECT_DIR' directory..."
  git clone "$REPO_URL" "$PROJECT_DIR" || handle_error "Git clone failed. Check the REPO_URL and your internet connection."
  cd "$PROJECT_DIR" || handle_error "Failed to enter $PROJECT_DIR directory after cloning."
fi
echo "✅ Repository ready."

# 2. Create Python virtual environment
echo "🐍 Creating Python virtual environment (venv)..."
python3 -m venv venv || handle_error "Failed to create virtual environment. Ensure Python 3 is installed correctly."
echo "✅ Virtual environment created."

# 3. Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || handle_error "Failed to activate virtual environment."
echo "✅ Virtual environment activated."

# 4. Install requirements
if [ -f "requirements.txt" ]; then
  echo "📦 Installing dependencies from requirements.txt..."
  pip install -r requirements.txt || handle_error "Failed to install requirements. Check requirements.txt and your internet connection."
  echo "✅ Dependencies installed."
else
  echo "⚠️ requirements.txt not found. Skipping dependency installation. Please ensure this file exists in your repository."
fi

# 5. Create template credentials.py
echo "🔑 Creating template credentials.py file..."
cat << EOF > credentials.py
# DMarket API Credentials
# IMPORTANT: Replace the placeholder values below with your actual DMarket API keys.

PUBLIC_KEY = "YOUR_PUBLIC_API_KEY_HERE"
SECRET_KEY = "YOUR_SECRET_API_KEY_HERE"
EOF

if [ -f "credentials.py" ]; then
    echo "✅ Template credentials.py created successfully."
else
    handle_error "Failed to create template credentials.py."
fi

echo ""
echo "🎉 Setup complete for dmarket_bot! 🎉"
echo ""
echo "👉 IMPORTANT NEXT STEP: 👈"
echo "You MUST edit the 'credentials.py' file located in the '$PROJECT_DIR' directory."
echo "Open it with a text editor and replace 'YOUR_PUBLIC_API_KEY_HERE' and 'YOUR_SECRET_API_KEY_HERE' with your actual DMarket API keys."
echo ""
echo "To run your bot (after editing credentials.py):"
echo "1. run main.py in your venv"
echo "2. There is no step 2, enjoy"
