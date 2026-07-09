import sqlite3
import json
import configparser

from flask import Blueprint, request, jsonify, g

from udp_comms import engine_sender

main_routes = Blueprint('main', __name__)

database_routes = Blueprint('database', __name__)

config = configparser.ConfigParser()
config.read('config.ini')

DATABASE = config.get('database', 'path', fallback='api/led_configs.db')

def get_db():
    db = getattr(g, '_database', None)
    print(DATABASE)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@main_routes.route('/api/status', methods=['GET'])
def status():
    request_payload = {"action": "get_status"}
    return engine_sender.request_from_engine(request_payload)

@main_routes.route('/api/brightness', methods=['POST'])
def brightness():
    return engine_sender.default_send_to_engine(request)

@main_routes.route('/api/animation', methods=['POST'])
def animation():
    return engine_sender.default_send_to_engine(request)

@main_routes.route('/api/clear', methods=['POST'])
def clear():
    return engine_sender.default_send_to_engine(request)

@main_routes.route('/api/power', methods=['POST'])
def power():
    return engine_sender.default_send_to_engine(request)

@main_routes.route('/api/pause', methods=['POST'])
def pause():
    return engine_sender.default_send_to_engine(request)

@main_routes.route('/api/config', methods=['POST'])
def config():
    return engine_sender.default_send_to_engine(request)

# -----------------------------------------------------------

# --- SAVE A CONFIG ---
@database_routes.route('/api/configs', methods=['POST'])
def save_config():
    payload = request.json
    name = payload.get('name')
    animations = payload.get('animations')

    if not name or not animations:
        return jsonify({"status": "error", "message": "Config name and animations list are required."}), 400

    db = get_db()
    try:
        # We use an UPSERT here. If a config with this name already exists, 
        # it updates the animations instead of throwing an error.
        db.execute('''
            INSERT INTO configs (name, animations_json) 
            VALUES (?, ?) 
            ON CONFLICT(name) DO UPDATE SET animations_json=excluded.animations_json
        ''', (name, json.dumps(animations))) # Convert the Python list to a JSON string
        
        db.commit()
        return jsonify({"status": "success", "message": f"Config '{name}' saved successfully."}), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- RETRIEVE ALL CONFIGS ---
@database_routes.route('/api/configs', methods=['GET'])
def get_configs():
    db = get_db()
    try:
        cursor = db.execute('SELECT name, animations_json FROM configs')
        rows = cursor.fetchall()
        
        # Rebuild the list of configs to send back to React
        saved_configs = []
        for row in rows:
            saved_configs.append({
                "name": row['name'],
                "animations": json.loads(row['animations_json']) # Convert JSON string back to a Python list
            })
            
        return jsonify({"status": "success", "data": saved_configs}), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- RETRIEVE A SINGLE CONFIG BY NAME ---
@database_routes.route('/api/configs/<config_name>', methods=['GET'])
def get_config(config_name):
    db = get_db()
    try:
        cursor = db.execute('SELECT name, animations_json FROM configs WHERE name = ?', (config_name,))
        row = cursor.fetchone()
        
        if row:
            config_data = {
                "name": row['name'],
                "animations": json.loads(row['animations_json']) # Convert JSON string back to a Python list
            }
            return jsonify({"status": "success", "data": config_data}), 200
        else:
            return jsonify({"status": "error", "message": f"Config '{config_name}' not found."}), 404
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- DELETE A CONFIG ---
@database_routes.route('/api/configs/<config_name>', methods=['DELETE'])
def delete_config(config_name):
    db = get_db()
    try:
        db.execute('DELETE FROM configs WHERE name = ?', (config_name,))
        db.commit()
        return jsonify({"status": "success", "message": f"Config '{config_name}' deleted."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500