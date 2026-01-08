#!/usr/bin/env python3
"""
Database Initialization Script
Run this to set up the database tables and optionally seed demo data.

Usage:
    python scripts/init_db.py           # Initialize tables only
    python scripts/init_db.py --seed    # Initialize tables + seed demo data
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import (
    init_database, 
    is_database_connected, 
    create_user, 
    save_interaction,
    get_database_url
)


def seed_demo_data():
    """Seed the database with demo users and sample interactions."""
    print("\n[*] Seeding demo data...")
    
    # Create demo users with passwords
    # Password for all demo users is 'demo123'
    demo_users = [
        ("USR_001", "user@demo.nl", "U", "demo123"),      # End-User
        ("USR_002", "researcher@demo.nl", "R", "demo123"), # Researcher
        ("USR_003", "admin@qog.nl", "R", "demo123"),       # Researcher/Admin
    ]
    
    for user_id, email, access_level, password in demo_users:
        success, msg = create_user(user_id, email, access_level, password)
        if success:
            print(f"  [OK] Created user: {email} ({access_level})")
        else:
            print(f"  [!] User {email}: {msg}")
    
    # Create sample interactions
    sample_interactions = [
        ("USR_001", 7.0, "Immigration policy effectiveness and border control measures"),
        ("USR_001", 6.0, "Healthcare system efficiency and hospital capacity"),
        ("USR_001", 8.0, "Education funding and school performance metrics"),
        ("USR_002", 5.0, "Infrastructure maintenance and road quality"),
        ("USR_002", 7.5, "Environmental protection and climate initiatives"),
    ]
    
    print("\n[*] Creating sample interactions...")
    for user_id, satisfaction, summary in sample_interactions:
        success, result = save_interaction(
            user_id=user_id,
            satisfaction_raw=satisfaction,
            summary=summary,
            correlation_index=None,  # Would be set by RAG system
            verification_flag='U'    # Unverified without RAG
        )
        if success:
            print(f"  [OK] Created interaction: {result}")
        else:
            print(f"  [X] Failed: {result}")


def main():
    print("=" * 50)
    print("Quality of Dutch Government - Database Setup")
    print("=" * 50)
    
    # Show database URL (masked password)
    db_url = get_database_url()
    display_url = db_url
    if '@' in db_url and ':' in db_url.split('@')[0]:
        # Mask password in display
        parts = db_url.split('@')
        pre_at = parts[0]
        if ':' in pre_at:
            protocol_user = pre_at.rsplit(':', 1)[0]
            display_url = f"{protocol_user}:****@{parts[1]}"
    
    print(f"\n[DB] Database: {display_url}")
    
    # Check connection
    print("\n[*] Testing connection...")
    if is_database_connected():
        print("  [OK] Database connection successful!")
    else:
        print("  [X] Failed to connect to database")
        print("\n[TIP] Tips:")
        print("  - For SQLite: No setup needed, file will be created automatically")
        print("  - For PostgreSQL: Make sure the server is running and database exists")
        print("  - Check your .env file for correct credentials")
        sys.exit(1)
    
    # Initialize tables
    print("\n[*] Initializing tables...")
    success, message = init_database()
    if success:
        print(f"  [OK] {message}")
    else:
        print(f"  [X] {message}")
        sys.exit(1)
    
    # Check for --seed flag
    if "--seed" in sys.argv:
        seed_demo_data()
    else:
        print("\n[TIP] Run with --seed to add demo data:")
        print("   python scripts/init_db.py --seed")
    
    print("\n" + "=" * 50)
    print("[OK] Database setup complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
