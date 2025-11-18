from flask import Blueprint, request, jsonify
from app.schemas.user import user_schema
from marshmallow import ValidationError
from . import service 
from app.schemas.login import login_schema


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        # Load data (với load_instance=False)
        data = user_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    # Gọi service, nó sẽ trả về (data, status_code)
    response_data, status_code = service.register_user(data) # Gọi hàm service
    
    return jsonify(response_data), status_code

@auth_bp.route('/login', methods=['POST'])
def login():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    # Validate (xác thực) input bằng LoginSchema
    try:
        data = login_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    # Gọi service login
    response_data, status_code = service.login_user(data)
    
    return jsonify(response_data), status_code