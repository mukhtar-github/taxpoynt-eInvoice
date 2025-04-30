"""
Script to generate SQL for creating encryption-related tables.

This script prints the SQL that can be used to create the encryption-related
tables in the database.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models.encryption import EncryptionKey, EncryptionConfig
from app.models.firs_credentials import FIRSCredentials
from app.models.api_keys import APIKey
from app.models.integration import Integration, IntegrationHistory
from app.db.base import Base
from sqlalchemy import create_engine, MetaData

def generate_create_tables_sql():
    """Generate SQL for creating encryption-related tables."""
    
    # Use a memory SQLite database to generate the schema
    engine = create_engine('sqlite:///:memory:')
    
    # Create tables in memory
    Base.metadata.create_all(engine)
    
    # Get only the encryption-related tables
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    tables = [
        'encryption_keys',
        'encryption_configs',
        'api_keys',
        'firs_credentials'
    ]
    
    # Generate SQL for each table
    sql_statements = []
    for table_name in tables:
        if table_name in metadata.tables:
            # Get the table definition
            table = metadata.tables[table_name]
            # Convert SQLite DDL to PostgreSQL
            create_stmt = str(table.create(bind=engine)).replace('AUTOINCREMENT', 'IDENTITY')
            sql_statements.append(create_stmt)
            
    # Generate SQL for altering integration tables
    sql_statements.append("""
-- Add encryption-related columns to integrations table
ALTER TABLE integrations 
ADD COLUMN config_encrypted BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN encryption_key_id VARCHAR(100) REFERENCES encryption_keys(id);

-- Add encryption-related columns to integration_history table
ALTER TABLE integration_history 
ADD COLUMN previous_config_encrypted BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN new_config_encrypted BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN encryption_key_id VARCHAR(100) REFERENCES encryption_keys(id);
    """)
    
    return "\n\n".join(sql_statements)

if __name__ == "__main__":
    sql = generate_create_tables_sql()
    print(sql)
    
    # Optionally write to a file
    output_file = os.path.join(os.path.dirname(__file__), "encryption_tables.sql")
    with open(output_file, "w") as f:
        f.write(sql)
    
    print(f"\nSQL written to {output_file}") 