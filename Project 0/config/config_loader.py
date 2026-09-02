"""
config_loader.py

Reads settings.yaml (project parameters) and .env (secrets),
and exposes a single Config object that every other script imports from.
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load .env into environment variables (os.environ)
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

# Path to this file's directory, so settings.yaml is found
# regardless of where the script is run FROM
CONFIG_DIR = Path(__file__).parent
SETTINGS_PATH = CONFIG_DIR / "settings.yaml"


def load_settings() -> dict:
    """Read settings.yaml and return it as a Python dict."""
    with open(SETTINGS_PATH, "r") as f:
        return yaml.safe_load(f)


def get_db_connection_string() -> str:
    """
    Build a SQLAlchemy-compatible PostgreSQL connection string
    from environment variables loaded via .env
    """
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME")

    if password:
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
    else:
        return f"postgresql+psycopg2://{user}@{host}:{port}/{dbname}"


# Load once at import time so other files can just do:
# from config.config_loader import SETTINGS
SETTINGS = load_settings()


if __name__ == "__main__":
    # Quick manual test: run this file directly to sanity-check everything loads
    print("Loaded settings:")
    print(SETTINGS)
    print("\nDB connection string:")
    print(get_db_connection_string())