import os, sys, json, requests
# launched as `python api/server.py`, so repo root isn't on sys.path; add it
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))  # APS creds from repo-root .env
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from impact.engine import compute_impact

app = Flask(__name__, static_folder='../viewer')
CORS(app)
DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

@app.route('/')
def serve_index(): return send_from_directory(app.static_folder, 'index.html')

@app.route('/static/<path:path>')
def serve_static(path): return send_from_directory(app.static_folder, path)

@app.route('/api/locations', methods=['GET'])
def get_locations():
    locations = load_json('locations.json')
    list_view = []
    for loc in locations:
        loc_copy = {k: v for k, v in loc.items() if k != 'repair_options'}
        loc_copy['violation_count'] = len(loc.get('violations', []))
        list_view.append(loc_copy)
    return jsonify(list_view)

@app.route('/api/location/<location_id>', methods=['GET'])
def get_location(location_id):
    locations = load_json('locations.json')
    for loc in locations:
        if loc['id'] == location_id: return jsonify(loc)
    return jsonify({"error": "Location not found"}), 404

@app.route('/api/impact/<location_id>/<repair_option_id>', methods=['GET'])
def get_impact(location_id, repair_option_id):
    locations = load_json('locations.json')
    location = next((loc for loc in locations if loc['id'] == location_id), None)
    if not location: return jsonify({"error": "Location not found"}), 404
    repair_option = next((rep for rep in location.get('repair_options', []) if rep['id'] == repair_option_id), None)
    if not repair_option: return jsonify({"error": "Repair option not found"}), 404
    return jsonify(compute_impact(location, repair_option))

@app.route('/api/urn/<location_id>/<variant>', methods=['GET'])
def get_urn(location_id, variant):
    urns = load_json('urns.json')
    key = f"{location_id}_{variant}"
    if key in urns: return jsonify({"urn": urns[key], "status": "ready"})
    return jsonify({"status": "processing"}), 202

@app.route('/api/config', methods=['GET'])
def get_config(): return jsonify({"client_id": os.getenv('APS_CLIENT_ID', '')})

@app.route('/api/token', methods=['GET'])
def get_token():
    client_id, client_secret = os.getenv('APS_CLIENT_ID'), os.getenv('APS_CLIENT_SECRET')
    if not client_id or not client_secret: return jsonify({"error": "APS credentials missing"}), 500
    auth_url = 'https://developer.api.autodesk.com/authentication/v2/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
    data = {'client_id': client_id, 'client_secret': client_secret, 'grant_type': 'client_credentials', 'scope': 'data:read'}
    resp = requests.post(auth_url, headers=headers, data=data)
    if resp.status_code == 200: return jsonify({"access_token": resp.json()['access_token']})
    return jsonify({"error": "Failed to authenticate with APS"}), resp.status_code

if __name__ == '__main__': app.run(port=5000)
