from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging

log = logging.getLogger('werkzeug')
log.disabled = True

FlaskApp = Flask(__name__, template_folder='templates')
CORS(FlaskApp, resources={r"/api/*": {"origins": ["http://127.0.0.1:5050", "*"]}})

global data
data = {}

@FlaskApp.route('/api/telescope/position', methods=['GET'])
def get_telescope_position():
    global data
    return data

@FlaskApp.route('/api/telescope/position', methods=['POST'])
def set_telescope_position():
    global data
    
    data = request.get_json()
    return jsonify({'status': 200})

@FlaskApp.route('/')
def home():    
    return render_template('index.html')