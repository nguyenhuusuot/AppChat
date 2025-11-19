# app/api/users/controller.py

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import socketio # Import biến socketio instance
from . import service

users_bp = Blueprint('users', __name__)

@users_bp.route('/friends', methods=['GET'])
@jwt_required()
def get_my_friends():
    current_user_id = get_jwt_identity()
    response_data, status_code = service.get_friends(current_user_id)
    return jsonify(response_data), status_code

@users_bp.route('/friends/pending', methods=['GET'])
@jwt_required()
def get_my_pending_requests():
    current_user_id = get_jwt_identity()
    response_data, status_code = service.get_pending_requests(current_user_id)
    return jsonify(response_data), status_code

@users_bp.route('/friends/<int:target_user_id>/add', methods=['POST'])
@jwt_required()
def send_request(target_user_id):
    current_user_id = get_jwt_identity()
    response_data, status_code = service.send_friend_request(current_user_id, target_user_id)
    return jsonify(response_data), status_code

@users_bp.route('/friends/accept/<int:sender_user_id>', methods=['POST'])
@jwt_required()
def accept_request(sender_user_id):
    current_user_id = get_jwt_identity()
    response_data, status_code = service.accept_friend_request(current_user_id, sender_user_id)
    return jsonify(response_data), status_code

@users_bp.route('/friends/<int:target_id>/cancel', methods=['DELETE'])
@jwt_required()
def cancel_request(target_id):
    current_user_id = get_jwt_identity()
    response, status = service.cancel_friend_request(current_user_id, target_id)
    return jsonify(response), status

@users_bp.route('/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    if 'file' not in request.files:
        return jsonify({"message": "Không tìm thấy file"}), 400
    file = request.files['file']
    user_id = get_jwt_identity()
    
    data, error, status = service.upload_user_avatar(user_id, file)
    
    if error: 
        return jsonify({"message": error}), status
    
    # --- ĐÃ SỬA: XÓA 'broadcast=True' ---
    # Mặc định socketio.emit từ controller sẽ gửi cho tất cả client
    socketio.emit('user_avatar_update', {
        'user_id': user_id, 
        'avatar': data['avatar_url']
    })
    
    return jsonify(data), status

@users_bp.route('/search', methods=['GET'])
@jwt_required()
def search_users():
    query = request.args.get('q', '')
    current_user_id = get_jwt_identity()
    data, error, status = service.search_users_by_query(query, current_user_id)
    if error: return jsonify({"message": error}), status
    return jsonify(data), status

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    API: Cập nhật thông tin cá nhân
    """
    current_user_id = get_jwt_identity()
    json_data = request.get_json()
    
    data, status = service.update_user_profile(current_user_id, json_data)
    
    if status == 200:
        # --- ĐÃ SỬA: XÓA 'broadcast=True' ---
        socketio.emit('user_info_update', {
            'user_id': current_user_id,
            'username': data['username'],
            'email': data['email']
        })
    
    return jsonify(data), status