"""
Backend API endpoints - Flask
"""
from flask import Flask, jsonify, request
from .models import User
from .auth import authenticate
from .calculator import calculate

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users."""
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@app.route('/api/users/<int:id>', methods=['GET'])
def get_user(id):
    """Get user by ID."""
    user = User.query.get(id)
    return jsonify(user.to_dict())

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create new user."""
    data = request.json
    user = User(**data)
    return jsonify(user.to_dict())

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint."""
    data = request.json
    result = authenticate(data['username'], data['password'])
    return jsonify(result)

@app.route('/api/calculate', methods=['GET'])
def calculate_endpoint():
    """Calculator endpoint."""
    a = request.args.get('a', type=int)
    b = request.args.get('b', type=int)
    return jsonify({'result': calculate(a, b)})
