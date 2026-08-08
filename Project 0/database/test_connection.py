"""
test_connection.py

One-time sanity check: can we actually connect to PostgreSQL
using the connection string built by config_loader?
"""

import sys
from pathlib import Path

# Add the project root to Python's search path so we can import
# from the 'config' folder, regardless of where this script is run from
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from config.config_loader import get_db_connection_string

engine = create_engine(get_db_connection_string())

with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print("Connected successfully!")
    print(result.fetchone())