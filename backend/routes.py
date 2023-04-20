from backend import app
from flask import request
from backend.models import User
from backend import db
import logging


logging.basicConfig(level=logging.DEBUG)


@app.route('/hello', methods=['GET', 'POST'])
def index():
    return "login"




@app.route('/', methods=["GET", "POST", "PUT"])
def create_user():
    if not request.is_json:
        return {'error': 'Your request content-type must be application/json'}, 400
    data = request.json
    required_fields = ['username', 'password']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    if missing_fields:
        return {'error': f"{', '.join(missing_fields)} must be in the request body"}, 400
    username = data.get('username')
    password = data.get('password')
    new_user = User(username=username, password=password)
    try:
        db.session.add(new_user)
        db.session.commit()
        logging.debug(f"User {username} created successfully!")
        return new_user.to_dict(), 201
    except Exception as e:
        return {'error': 'Could not create user'}, 500
    # return new_user.to_dict(), 201

    

@app.route('/login', methods=["POST"])
def login():
    if not request.is_json:
        return {'error': 'Your request content-type must be application/json'}, 400
    data = request.json
    required_fields = ['username', 'password']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    if missing_fields:
        return {'error': f"{', '.join(missing_fields)} must be in the request body"}, 400
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        return {'message': f"User {username} logged in successfully!"}, 200
    else:
        logging.debug(f"Invalid username or password!")
        return {'error': 'Invalid username or password!'}, 401





@app.route('/user', methods=["GET", 'PUT'])
def update_user(username):
    if not request.is_json:
        return {'error': 'Your request content-type must be application/json'}, 400
    data = request.json
    new_username = data.get('new_username')
    if not new_username:
        return {'error': 'At least one field must be provided'}, 400
    user = User.query.filter_by(username=username).first()
    if not user:
        return {'error': f'User with username {username} not found'}, 404
    user.username = new_username
    try:
        db.session.commit()
        return user.to_dict(), 200
    except Exception as e:
        return {'error': 'Could not update user'}, 500