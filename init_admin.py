"""
Auto-create admin user on first run (for Railway deployment)
Creates admin with default password: Atlas2025!
CHANGE THIS PASSWORD after first login via admin panel!
"""
import os
import sys

# Check if admin already exists
try:
    from auth import get_user, create_user, UserCreate

    if get_user("admin"):
        print("Admin user already exists")
        sys.exit(0)

    # Create admin user with secure default password
    # User MUST change this after first login!
    admin_password = os.environ.get("ADMIN_PASSWORD", "Atlas2025!")

    admin_user = create_user(UserCreate(
        username="admin",
        password=admin_password,
        email="admin@atlas.com",
        full_name="Admin User",
        is_admin=True
    ))

    print("")
    print("=" * 60)
    print("  ATLAS TERMINAL - Admin User Created!")
    print("=" * 60)
    print(f"  Username: {admin_user.username}")
    print(f"  Password: {admin_password}")
    print("")
    print("  IMPORTANT: Change this password after first login!")
    print("  Login at: https://atlas-terminal.net/login.html")
    print("=" * 60)
    print("")

except Exception as e:
    print(f"Note: Admin creation: {e}")
    # Don't exit with error - backend should still start
    sys.exit(0)
