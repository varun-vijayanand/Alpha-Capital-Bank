"""
main.py

Single entry point for Project 0: regenerates the entire Alpha Capital
Bank synthetic dataset and loads it fresh into PostgreSQL.

Usage:
    python main.py
"""

from database.load_data import main as load_data_main


if __name__ == "__main__":
    load_data_main()