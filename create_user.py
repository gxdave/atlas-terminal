"""
Atlas Terminal - User Creation CLI Tool
Simple command-line tool for creating users
"""

import sys
import getpass
from auth import create_user, UserCreate, get_all_users, init_database

def main():
    print("=" * 60)
    print("      ATLAS TERMINAL - USER MANAGEMENT")
    print("=" * 60)
    print()

    while True:
        print("\nOptions:")
        print("1. Create new user")
        print("2. List all users")
        print("3. Exit")
        print()

        choice = input("Select option: ").strip()

        if choice == "1":
            create_user_interactive()
        elif choice == "2":
            list_all_users()
        elif choice == "3":
            print("\nExiting...")
            break
        else:
            print("Invalid choice. Please try again.")

def create_user_interactive():
    """Create user interactively"""
    print("\n--- CREATE NEW USER ---")

    username = input("Username: ").strip()
    if not username:
        print("Error: Username cannot be empty")
        return

    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Confirm Password: ")

    if password != password_confirm:
        print("Error: Passwords do not match")
        return

    if len(password) < 6:
        print("Error: Password must be at least 6 characters")
        return

    full_name = input("Full Name (optional): ").strip() or None
    email = input("Email (optional): ").strip() or None

    is_admin_input = input("Admin user? (y/n): ").strip().lower()
    is_admin = is_admin_input == "y"

    try:
        user = create_user(UserCreate(
            username=username,
            password=password,
            full_name=full_name,
            email=email,
            is_admin=is_admin
        ))

        print(f"\n✓ User created successfully!")
        print(f"  Username: {user.username}")
        print(f"  Full Name: {user.full_name or 'N/A'}")
        print(f"  Email: {user.email or 'N/A'}")
        print(f"  Admin: {'Yes' if user.is_admin else 'No'}")
        print(f"\nCredentials:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print(f"\nShare these credentials with your user.")

    except ValueError as e:
        print(f"\nError: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")

def list_all_users():
    """List all existing users"""
    print("\n--- ALL USERS ---")

    try:
        users = get_all_users()

        if not users:
            print("No users found.")
            return

        print(f"\nTotal users: {len(users)}\n")
        print(f"{'Username':<20} {'Full Name':<25} {'Email':<30} {'Admin':<6} {'Status':<8}")
        print("-" * 95)

        for user in users:
            status = "Disabled" if user.disabled else "Active"
            admin = "Yes" if user.is_admin else "No"
            print(f"{user.username:<20} {user.full_name or 'N/A':<25} {user.email or 'N/A':<30} {admin:<6} {status:<8}")

    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    # Initialize database
    init_database()

    # Check if arguments provided
    if len(sys.argv) > 1:
        # Non-interactive mode
        if sys.argv[1] == "create":
            if len(sys.argv) < 4:
                print("Usage: python create_user.py create <username> <password> [--admin] [--email <email>] [--name <name>]")
                sys.exit(1)

            username = sys.argv[2]
            password = sys.argv[3]
            is_admin = "--admin" in sys.argv
            email = None
            full_name = None

            if "--email" in sys.argv:
                idx = sys.argv.index("--email")
                email = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None

            if "--name" in sys.argv:
                idx = sys.argv.index("--name")
                full_name = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None

            try:
                user = create_user(UserCreate(
                    username=username,
                    password=password,
                    email=email,
                    full_name=full_name,
                    is_admin=is_admin
                ))
                print(f"User '{username}' created successfully.")
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)

        elif sys.argv[1] == "list":
            list_all_users()

        else:
            print("Unknown command. Use 'create' or 'list'.")
            sys.exit(1)
    else:
        # Interactive mode
        main()
