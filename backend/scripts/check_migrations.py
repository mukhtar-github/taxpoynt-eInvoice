#!/usr/bin/env python
"""
Migration helper script for TaxPoynt eInvoice

This script checks for multiple migration heads and assists in
resolving them before new migrations are created.
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

def run_command(cmd):
    """Run a shell command and return the output."""
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout.decode('utf-8'), stderr.decode('utf-8'), process.returncode

def check_heads():
    """Check if there are multiple migration heads."""
    stdout, stderr, returncode = run_command("alembic heads")
    if returncode != 0:
        print(f"Error checking migration heads: {stderr}")
        sys.exit(1)
    
    heads = stdout.strip().split('\n')
    # Filter out empty lines or descriptive text
    heads = [h for h in heads if h and h.strip().startswith('Rev:')]
    
    if len(heads) > 1:
        print(f"WARNING: Found {len(heads)} migration heads!")
        print("\n".join(heads))
        print("\nMultiple heads can cause deployment issues in Railway.")
        return True
    else:
        print("✅ Single migration head found. Migration tree is clean.")
        return False

def merge_heads():
    """Merge multiple migration heads."""
    merge_name = f"merge_migrations_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"\n🔄 Creating merge migration: {merge_name}...")
    stdout, stderr, returncode = run_command(f"alembic merge heads -m {merge_name}")
    
    if returncode != 0:
        print(f"❌ Error creating merge migration: {stderr}")
        sys.exit(1)
    
    print(f"✅ Successfully created merge migration: {stdout}")
    return True

def create_migration(name):
    """Create a new migration with the given name."""
    stdout, stderr, returncode = run_command(f"alembic revision -m {name}")
    
    if returncode != 0:
        print(f"❌ Error creating migration: {stderr}")
        sys.exit(1)
    
    print(f"✅ Successfully created migration: {stdout}")
    return True

def main():
    parser = argparse.ArgumentParser(description="TaxPoynt eInvoice Migration Helper")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check migration heads')
    
    # Merge command
    merge_parser = subparsers.add_parser('merge', help='Merge migration heads')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new migration')
    create_parser.add_argument('name', help='Name of the migration')
    
    # Safe-create command (checks for multiple heads first)
    safe_create_parser = subparsers.add_parser('safe-create', 
                                              help='Check for multiple heads and create a new migration')
    safe_create_parser.add_argument('name', help='Name of the migration')
    
    args = parser.parse_args()
    
    # Set current directory to backend directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    os.chdir(backend_dir)
    
    if args.command == 'check':
        check_heads()
    elif args.command == 'merge':
        if check_heads():
            merge_heads()
        else:
            print("No merge needed. You have a single migration head.")
    elif args.command == 'create':
        create_migration(args.name)
    elif args.command == 'safe-create':
        has_multiple_heads = check_heads()
        
        if has_multiple_heads:
            print("\nWARNING: You have multiple migration heads.")
            response = input("Do you want to merge them before creating a new migration? (y/n): ")
            
            if response.lower() == 'y':
                merge_heads()
            else:
                print("Continuing without merging heads. This may cause deployment issues.")
        
        create_migration(args.name)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
