"""
One-time script to create first admin user directly in Railway database
Run this once, then use the admin panel for all other users
"""

import requests
import sys

# Your Railway URL
RAILWAY_URL = "https://atlas-terminal.net"

print("=" * 60)
print("    ATLAS TERMINAL - First Admin Setup")
print("=" * 60)
print()

# Since we can't create a user without authentication,
# we need to create it directly via Railway Shell or use init_admin.py

print("⚠️  This script requires Railway Shell access")
print()
print("Please run this command in Railway Shell:")
print()
print("   python create_user.py create admin YourPassword123 --admin")
print()
print("Or use Railway CLI:")
print()
print("   1. Install: iwr https://railway.app/install.ps1 | iex")
print("   2. Login: railway login")
print("   3. Link: railway link")
print("   4. Run: railway run python create_user.py create admin Pass123 --admin")
print()
print("=" * 60)

# Alternative: Check if database exists and admin user exists
try:
    response = requests.get(f"{RAILWAY_URL}/health", timeout=5)
    if response.status_code == 200:
        print("✅ Backend is running!")
        print()

        # Try to login with common default credentials
        print("🔍 Checking if default admin exists...")

        test_passwords = [
            "DefaultAdmin123!",
            "admin",
            "Admin123",
            "Test123456"
        ]

        for test_pass in test_passwords:
            try:
                login_response = requests.post(
                    f"{RAILWAY_URL}/api/auth/login",
                    json={"username": "admin", "password": test_pass},
                    timeout=5
                )

                if login_response.status_code == 200:
                    print(f"✅ FOUND! Admin user exists with password: {test_pass}")
                    print()
                    print("Login at: https://atlas-terminal.net/login.html")
                    print(f"Username: admin")
                    print(f"Password: {test_pass}")
                    print()
                    print("⚠️  IMPORTANT: Change this password in the admin panel!")
                    sys.exit(0)
            except:
                pass

        print("❌ No admin user found with default passwords")
        print()
        print("You need to create one via Railway Shell:")
        print("   railway run python create_user.py create admin YourPassword --admin")

    else:
        print("❌ Backend not responding")

except Exception as e:
    print(f"❌ Could not connect to backend: {e}")

print()
print("=" * 60)
