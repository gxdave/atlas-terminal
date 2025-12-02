#!/bin/bash

# Atlas Terminal - Railway Deployment Script
# Deployt den Yield Spread Analyzer mit FRED API Integration

echo "=========================================="
echo "Atlas Terminal - Railway Deployment"
echo "=========================================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null
then
    echo "❌ Railway CLI not found!"
    echo ""
    echo "Install it with:"
    echo "  npm install -g @railway/cli"
    echo ""
    exit 1
fi

# Check if FRED_API_KEY is set
if [ -z "$FRED_API_KEY" ]; then
    echo "⚠️  FRED_API_KEY not set in environment"
    echo ""
    read -p "Enter your FRED API Key (or press Enter to skip): " fred_key

    if [ ! -z "$fred_key" ]; then
        export FRED_API_KEY=$fred_key
        echo "✓ FRED_API_KEY set"
    else
        echo "⚠️  Skipping FRED_API_KEY - you'll need to set it in Railway Dashboard"
    fi
else
    echo "✓ FRED_API_KEY found in environment"
fi

echo ""
echo "Step 1: Checking requirements..."

# Check if requirements.txt has necessary dependencies
if grep -q "fredapi" requirements.txt; then
    echo "✓ fredapi found in requirements.txt"
else
    echo "❌ fredapi not found in requirements.txt"
    exit 1
fi

if grep -q "scipy" requirements.txt; then
    echo "✓ scipy found in requirements.txt"
else
    echo "❌ scipy not found in requirements.txt"
    exit 1
fi

echo ""
echo "Step 2: Git status..."
git status --short

echo ""
read -p "Commit and push changes? (y/n): " commit_choice

if [ "$commit_choice" = "y" ]; then
    echo ""
    read -p "Enter commit message: " commit_msg

    if [ -z "$commit_msg" ]; then
        commit_msg="Update Yield Spread Analyzer with FRED API"
    fi

    git add .
    git commit -m "$commit_msg"
    git push

    echo "✓ Changes committed and pushed"
else
    echo "⚠️  Skipping git commit"
fi

echo ""
echo "Step 3: Railway Deployment..."

# Check if logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "Not logged in to Railway. Logging in..."
    railway login
fi

echo ""
echo "Current Railway project:"
railway status

echo ""
read -p "Deploy to Railway? (y/n): " deploy_choice

if [ "$deploy_choice" = "y" ]; then
    echo ""
    echo "Deploying..."
    railway up --detach

    echo ""
    echo "✓ Deployment initiated"

    # Set FRED_API_KEY if provided
    if [ ! -z "$FRED_API_KEY" ]; then
        echo ""
        echo "Setting FRED_API_KEY environment variable..."
        railway variables set FRED_API_KEY="$FRED_API_KEY"
        echo "✓ FRED_API_KEY set"
    fi

    echo ""
    echo "Step 4: Monitoring deployment..."
    echo ""
    echo "View logs with:"
    echo "  railway logs"
    echo ""
    echo "View project in browser:"
    echo "  railway open"
    echo ""

    read -p "Open logs now? (y/n): " logs_choice

    if [ "$logs_choice" = "y" ]; then
        railway logs
    fi
else
    echo "⚠️  Deployment cancelled"
fi

echo ""
echo "=========================================="
echo "Deployment script completed"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify deployment in Railway Dashboard"
echo "2. Check FRED_API_KEY is set: railway variables"
echo "3. Test health endpoint: https://your-app.railway.app/health"
echo "4. Test Yield Spread Analyzer in frontend"
echo ""
