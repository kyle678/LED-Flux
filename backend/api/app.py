from flask import Flask, g
from flask_cors import CORS
import configparser
import sqlite3

from routes import main_routes, database_routes

config = configparser.ConfigParser()
config.read('config.ini')

HOST = config.get('flask', 'host', fallback='0.0.0.0')
PORT = config.get('flask', 'port', fallback=5000)

DATABASE = config.get('database', 'path', fallback='api/led_configs.db')

app = Flask(__name__)
CORS(app)

app.register_blueprint(main_routes)
app.register_blueprint(database_routes)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # This lets us access columns by name (e.g., row['name'])
    return db

# 2. Automatically close the connection when the request finishes
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                animations_json TEXT NOT NULL
            )
        ''')
        db.commit()

if __name__ == '__main__':
    init_db()
    app.run(host=HOST, port=PORT)