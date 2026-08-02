"""
Migration cleanup script to remove problematic migrations
that reference deleted apps (runtime, rules, workflow)
"""
import os
import glob

def cleanup_migrations():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Remove all governance migrations except __init__.py
    governance_migrations_dir = os.path.join(base_dir, "apps", "governance", "migrations")
    
    if os.path.exists(governance_migrations_dir):
        print(f"Cleaning up governance migrations in: {governance_migrations_dir}")
        
        for file in os.listdir(governance_migrations_dir):
            if file.endswith(".py") and file != "__init__.py":
                file_path = os.path.join(governance_migrations_dir, file)
                print(f"Deleting: {file}")
                os.remove(file_path)
                print(f"✓ Deleted {file}")
    
    print("\n✓ Migration cleanup complete!")
    print("\n" + "="*60)
    print("Next steps:")
    print("="*60)
    print("1. Run: python manage.py makemigrations")
    print("2. Run: python manage.py migrate")
    print("\nNote: If you have an existing database with old migrations,")
    print("you may need to run: python manage.py migrate --fake governance zero")
    print("before step 1 to reset the migration state.")
    print("="*60)

if __name__ == "__main__":
    cleanup_migrations()
