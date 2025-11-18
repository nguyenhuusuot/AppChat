from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import service 

users_bp = Blueprint('users', __name__)

@users_bp.route('/friends', methods=['GET'])
@jwt_required()
def get_my_friends():
    # API: Lấy danh sách bạn bè đã chấp nhận
    current_user_id = get_jwt_identity()
    response_data, status_code = service.get_friends(current_user_id)
    return jsonify(response_data), status_code

@users_bp.route('/friends/pending', methods=['GET'])
@jwt_required()
def get_my_pending_requests():
    # API: Lấy danh sách lời mời đang chờ
    current_user_id = get_jwt_identity()
    response_data, status_code = service.get_pending_requests(current_user_id)
    return jsonify(response_data), status_code

@users_bp.route('/friends/<int:target_user_id>/add', methods=['POST'])
@jwt_required()
def send_request(target_user_id):
    # API: Gửi lời mời kết bạn tới một user
    current_user_id = get_jwt_identity()
    response_data, status_code = service.send_friend_request(current_user_id, target_user_id)
    return jsonify(response_data), status_code

@users_bp.route('/friends/accept/<int:sender_user_id>', methods=['POST'])
@jwt_required()
def accept_request(sender_user_id):
    # API: Chấp nhận lời mời từ một user
    current_user_id = get_jwt_identity()
    response_data, status_code = service.accept_friend_request(current_user_id, sender_user_id)
    return jsonify(response_data), status_code