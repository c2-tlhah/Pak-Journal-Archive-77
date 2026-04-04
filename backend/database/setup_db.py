#!/usr/bin/env python3
"""
Database setup script
Creates database and initializes schema
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import sys

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'pak_journal_archive')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

def create_database():
    """Create database if it doesn't exist"""
    try:
        # Connect to postgres database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database='postgres',
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE {DB_NAME}')
            print(f"[OK] Database '{DB_NAME}' created successfully")
        else:
            print(f"[OK] Database '{DB_NAME}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[FAIL] Failed to create database: {e}")
        return False

def initialize_schema():
    """Initialize database schema from schema.sql"""
    try:
        # Connect to our database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # Read and execute schema file
        schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        conn.commit()
        
        print("[OK] Database schema initialized successfully")
        print("[OK] Default admin user created (username: admin, password: admin123)")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[FAIL] Failed to initialize schema: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("PAK JOURNAL ARCHIVE 77 - Database Setup")
    print("=" * 60)
    
    print(f"\nDatabase Configuration:")
    print(f"  Host: {DB_HOST}")
    print(f"  Port: {DB_PORT}")
    print(f"  Database: {DB_NAME}")
    print(f"  User: {DB_USER}")
    
    print("\nStep 1: Creating database...")
    if not create_database():
        sys.exit(1)
    
    print("\nStep 2: Initializing schema...")
    if not initialize_schema():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("[OK] Database setup completed successfully!")
    print("=" * 60)
    print("\nYou can now start the backend server with: python3 app.py")
    print("\nDefault admin credentials:")
    print("  Email: admin@pakjournal77.com")
    print("  Password: admin123")
    print("  (Please change this password after first login)")

if __name__ == '__main__':
    main()
