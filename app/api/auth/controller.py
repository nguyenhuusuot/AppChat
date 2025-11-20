from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
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
        # Load data
        data = user_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    # Gọi service, nó sẽ trả về (data, status_code)
    response_data, status_code = service.register_user(data)
    
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

@auth_bp.route('/me', methods=['GET'])
@jwt_required() # Bắt buộc phải có Token hợp lệ mới được vào
def me():
    # API Lấy thông tin người dùng hiện tại
    
    # Lấy ID user từ trong Token (đã được giải mã)
    current_user_id = get_jwt_identity()
    
    # Gọi Service để lấy thông tin chi tiết từ Database
    response_data, status_code = service.get_me(current_user_id)
    
    return jsonify(response_data), status_code