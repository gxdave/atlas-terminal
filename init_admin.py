"""
Auto-create admin user on first run (for Railway deployment)
"""
import os
import sys

# Only run on Railway (check for PORT environment variable)
if not os.environ.get("PORT"):
    print("Not running on Railway, skipping admin creation")
    sys.exit(0)

# Check if admin already exists
from auth import get_user, create_user, UserCreate

if get_user("admin"):
    print("Admin user already exists, skipping creation")
    sys.exit(0)

# Create admin user with environment variable password
admin_password = os.environ.get("ADMIN_PASSWORD", "DefaultAdmin123!")

try:
    admin_user = create_user(UserCreate(
        username="admin",
        password=admin_password,
        email="admin@atlas.com",
        full_name="Admin User",
        is_admin=True
    ))
    print(f"✅ Admin user created successfully!")
    print(f"   Username: {admin_user.username}")
    print(f"   Password: {admin_password}")
    print(f"\n⚠️  IMPORTANT: Change this password after first login!")
except Exception as e:
    print(f"❌ Error creating admin user: {e}")
    sys.exit(1)
