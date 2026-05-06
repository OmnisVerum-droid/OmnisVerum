#!/usr/bin/env python3
"""
Omnisverum V1 Reset Script
Completely clears all data for a fresh start.
"""

import os
import shutil
import sqlite3
from pathlib import Path

def reset_database():
    """Remove SQLite database file."""
    db_files = ["omnisverum.db"]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"Removed {db_file}")

def reset_chromadb():
    """Remove ChromaDB persistence directory."""
    chroma_dirs = ["chroma_db", "./chroma_db"]
    
    for chroma_dir in chroma_dirs:
        if os.path.exists(chroma_dir):
            try:
                shutil.rmtree(chroma_dir)
                print(f"Removed {chroma_dir}")
            except PermissionError:
                print(f"Could not remove {chroma_dir} (permission denied)")

def reset_cache():
    """Remove cache directories."""
    cache_dirs = ["__pycache__", ".pytest_cache"]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"Removed {cache_dir}")
            except PermissionError:
                print(f"Could not remove {cache_dir} (permission denied)")

def reset_python_cache():
    """Remove all Python cache files."""
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".pyc") or file.endswith(".pyo"):
                try:
                    os.remove(os.path.join(root, file))
                except PermissionError:
                    pass
        if "__pycache__" in dirs:
            try:
                shutil.rmtree(os.path.join(root, "__pycache__"))
            except PermissionError:
                pass

def main():
    """Perform complete reset."""
    print("Resetting Omnisverum V1 to clean state...")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Reset all data
    reset_database()
    reset_chromadb()
    reset_cache()
    reset_python_cache()
    
    print("=" * 50)
    print("Reset complete! The application will start with:")
    print("   - Empty database")
    print("   - Fresh ChromaDB collections")
    print("   - No cached data")
    print("   - Clean Python bytecode")
    print("\nReady for V1 startup!")

if __name__ == "__main__":
    main()
