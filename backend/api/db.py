import sqlite3
import configparser

from flask import g

config = configparser.ConfigParser()
config.read('config.ini')

DATABASE = config.get('database', 'path', fallback='api/led_configs.db')

def get_db():
    """Per-request SQLite connection, closed by app.py's teardown hook."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # This lets us access columns by name (e.g., row['name'])
    return db
