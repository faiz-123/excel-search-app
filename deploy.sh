#!/bin/bash

echo "🚀 Excel Search App - Quick Deploy Script"
echo "========================================="

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Installing..."
    echo "Please install Heroku CLI first:"
    echo "🍎 macOS: brew install heroku/brew/heroku"
    echo "🐧 Linux: curl https://cli-assets.heroku.com/install.sh | sh"
    echo "🪟 Windows: Download from https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

echo "✅ Heroku CLI found"

# Login to Heroku
echo "🔐 Logging into Heroku..."
heroku login

# Create Heroku app
echo "📱 Creating Heroku app..."
read -p "Enter your app name (e.g., my-excel-search): " APP_NAME

if [[ -z "$APP_NAME" ]]; then
    APP_NAME="excel-search-$(date +%s)"
    echo "Using default name: $APP_NAME"
fi

heroku create $APP_NAME

# Deploy to Heroku
echo "🚀 Deploying to Heroku..."
git push heroku main

# Get app URL
APP_URL=$(heroku info -s | grep web-url | cut -d= -f2)

echo ""
echo "🎉 Deployment Complete!"
echo "========================"
echo "Your Excel Search App is now live at:"
echo "🌐 $APP_URL"
echo ""
echo "You can now:"
echo "✅ Access it from any device with internet"
echo "✅ Search your Excel data from anywhere"
echo "✅ Share the URL with others"
echo ""
echo "To update your app later:"
echo "1. Make changes to your code"
echo "2. Run: git add . && git commit -m 'Updated'"
echo "3. Run: git push heroku main"
echo ""
echo "Happy searching! 🔍"
