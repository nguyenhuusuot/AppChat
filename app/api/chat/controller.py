from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import socketio
from . import service

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/private', methods=['POST'])
@jwt_required()
def start_private_chat():
    # API: Bắt đầu chat với ai đó (Nhận target_user_id từ body JSON)

    current_user_id = str(get_jwt_identity()) # Đảm bảo là string hoặc int tùy setup
    
    json_data = request.get_json()
    target_id = json_data.get('target_user_id')
    
    if not target_id:
        return jsonify({"message": "Thiếu target_user_id"}), 400

    response, code = service.get_or_create_private_room(int(current_user_id), int(target_id))
    return jsonify(response), code

@chat_bp.route('/rooms/<int:room_id>/messages', methods=['GET'])
@jwt_required()
def get_history(room_id):
    # API: Lấy lịch sử tin nhắn
    # Query Params: ?page=1&per_page=20

    current_user_id = get_jwt_identity()
    
    # Lấy tham số phân trang từ URL
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    response, code = service.get_room_messages(current_user_id, room_id, page, per_page)
    return jsonify(response), code

@chat_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_chat_image():
    """
    API: Upload ảnh để gửi trong tin nhắn
    Method: POST
    Form-data: key='file' (file ảnh)
    """
    # 1. Kiểm tra xem request có file không
    if 'file' not in request.files:
        return jsonify({"message": "Không tìm thấy file trong request"}), 400
        
    file = request.files['file']
    user_id = get_jwt_identity()
    
    # 2. Gọi Service xử lý logic upload (đã được tách ra service ở bước trước)
    data, error, status = service.upload_chat_file(file, user_id)
    
    if error:
        return jsonify({"message": error}), status
        
    return jsonify(data), status

@chat_bp.route('/groups', methods=['GET'])
@jwt_required()
def get_groups():
    """
    API: Lấy danh sách nhóm chat của tôi
    """
    current_user_id = get_jwt_identity()
    response, code = service.get_user_groups(current_user_id)
    return jsonify(response), code

@chat_bp.route('/group', methods=['POST'])
@jwt_required()
def create_group():
    """
    API: Tạo nhóm chat
    Body: { "name": "Team Dev", "members": [2, 3, 5] }
    """
    current_user_id = get_jwt_identity()
    json_data = request.get_json()
    
    group_name = json_data.get('name')
    member_ids = json_data.get('members', []) # List các ID
    
    response, code = service.create_group_chat(int(current_user_id), group_name, member_ids)
    return jsonify(response), code

@chat_bp.route('/group/<int:group_id>', methods=['DELETE'])
@jwt_required()
def delete_group(group_id):
    """
    API: Xóa nhóm chat
    """
    current_user_id = get_jwt_identity()
    response, code = service.delete_group_chat(current_user_id, group_id)
    
    if code == 200:
        # Báo cho tất cả thành viên trong phòng biết nhóm đã bị xóa
        socketio.emit('group_deleted', {'group_id': group_id}, to=str(group_id))
        
    return jsonify(response), code


@chat_bp.route('/group/<int:group_id>/leave', methods=['POST'])
@jwt_required()
def leave_group(group_id):
    """
    API: Rời khỏi nhóm chat
    """
    current_user_id = get_jwt_identity()
    response, code = service.leave_group_chat(current_user_id, group_id)
    
    if code == 200:
        # Báo cho những người còn lại trong phòng biết
        socketio.emit('new_message', {
            'content': f"Một thành viên đã rời nhóm.",
            'sender': {'username': 'Hệ thống', 'id': 0, 'avatar': None},
            'timestamp': 'now',
            'room_id': group_id
        }, to=str(group_id))
        
    return jsonify(response), code