from flask import Flask, g
from flask_cors import CORS
import configparser

from db import get_db
from routes import main_routes, database_routes

config = configparser.ConfigParser()
config.read('config.ini')

HOST = config.get('flask', 'host', fallback='0.0.0.0')
# getint: app.run(port=...) needs an int, and config values come back as strings
PORT = config.getint('flask', 'port', fallback=5000)

app = Flask(__name__)
CORS(app)

app.register_blueprint(main_routes)
app.register_blueprint(database_routes)

# Automatically close the connection when the request finishes
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

# Run at import time (not just under __main__) so the table also gets
# created when the app is served by a WSGI server like gunicorn
init_db()

if __name__ == '__main__':
    app.run(host=HOST, port=PORT)