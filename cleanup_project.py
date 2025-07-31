#!/usr/bin/env python3
"""
Clean up all test files and unnecessary files from the project
"""

import os
import shutil

def cleanup_project():
    print("🧹 CLEANING UP PROJECT FILES")
    print("="*50)
    
    # Files to delete (test files, temp files, etc.)
    files_to_delete = [
        # Test files
        "test_booking_system.py",
        "test_database_booking.py", 
        "test_enhancements.py",
        "test_login.py",
        "test_multiple_booking.py",
        "test_registration.py",
        
        # Setup/migration files (no longer needed)
        "add_sample_data.py",
        "create_admin.py",
        "create_admin_realtime.py", 
        "create_admin_simple.py",
        "create_test_accounts.py",
        "fix_mobile_numbers.py",
        "migrate_database.py",
        "rename_admin.py",
        "setup_dummy_data.py",
        "update_email_fields.py",
        
        # Debug/utility files
        "debug_db.py",
        "export_data.py",
        "force_delete_all_lots.py",
        "tempCodeRunnerFile.py",
        
        # Old app versions
        "app.py",
        "admin.py",
        
        # Zip files
        "admin side.zip",
        "user side.zip",
        
        # Documentation files (keeping only README.md)
        "BACKEND_ENHANCEMENT_SUMMARY.md",
        "ENHANCEMENT_SUMMARY.md",
        "MULTIPLE_BOOKING_GUIDE.md"
    ]
    
    # Directories to clean up
    dirs_to_check = [
        "controllers/__pycache__",
        "models/__pycache__",
        "instance"  # Contains old database files
    ]
    
    deleted_files = []
    deleted_dirs = []
    
    # Delete files
    for file_name in files_to_delete:
        file_path = os.path.join(".", file_name)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_files.append(file_name)
                print(f"✅ Deleted file: {file_name}")
            except Exception as e:
                print(f"❌ Failed to delete {file_name}: {e}")
        else:
            print(f"⚠️  File not found: {file_name}")
    
    # Delete directories
    for dir_name in dirs_to_check:
        dir_path = os.path.join(".", dir_name)
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                deleted_dirs.append(dir_name)
                print(f"✅ Deleted directory: {dir_name}")
            except Exception as e:
                print(f"❌ Failed to delete {dir_name}: {e}")
    
    print("\n" + "="*50)
    print("🎉 CLEANUP COMPLETE!")
    print(f"📁 Files deleted: {len(deleted_files)}")
    print(f"📂 Directories deleted: {len(deleted_dirs)}")
    
    print("\n📋 REMAINING CORE FILES:")
    remaining_files = []
    for item in os.listdir("."):
        if os.path.isfile(item) and not item.startswith('.'):
            remaining_files.append(item)
    
    for file in sorted(remaining_files):
        print(f"   📄 {file}")
    
    print("\n📋 REMAINING DIRECTORIES:")
    remaining_dirs = []
    for item in os.listdir("."):
        if os.path.isdir(item) and not item.startswith('.'):
            remaining_dirs.append(item)
    
    for dir in sorted(remaining_dirs):
        print(f"   📁 {dir}/")

if __name__ == "__main__":
    cleanup_project()
