import os
from flask import current_app
from app import db
from app.models.room import Room
from app.models.participant import Participant
from app.models.message import Message
from app.models.user import User,friendship
from app.schemas.message import messages_schema,message_schema,room_schema,rooms_schema
from sqlalchemy import and_, func, or_
from werkzeug.utils import secure_filename
from sqlalchemy.orm import aliased

def get_or_create_private_room(current_user_id, target_user_id):
    # 1. Kiểm tra cơ bản
    if current_user_id == target_user_id:
        return {"message": "Không thể chat với chính mình"}, 400

    if not User.query.get(target_user_id):
        return {"message": "Người dùng không tồn tại"}, 404

    # 2. KIỂM TRA QUAN HỆ BẠN BÈ (Logic bạn yêu cầu)
    # Phải là bạn bè (status='accepted') mới được chat
    is_friend = db.session.query(friendship).filter(
        or_(
            # Chiều 1: Mình gửi, Họ nhận, Đã chấp nhận
            and_(
                friendship.c.user_id == current_user_id, 
                friendship.c.friend_id == target_user_id,
                friendship.c.status == 'accepted'
            ),
            # Chiều 2: Họ gửi, Mình nhận, Đã chấp nhận
            and_(
                friendship.c.user_id == target_user_id, 
                friendship.c.friend_id == current_user_id,
                friendship.c.status == 'accepted'
            )
        )
    ).first()

    if not is_friend:
        return {"message": "Hai người chưa là bạn bè, không thể nhắn tin."}, 403 # 403 Forbidden

    # 3. TÌM PHÒNG ĐÃ TỒN TẠI
    # Sử dụng Self-Join với 'aliased' để tìm chính xác phòng chung (Tránh lỗi trùng phòng)
    Participant1 = aliased(Participant)
    Participant2 = aliased(Participant)
    
    common_room = db.session.query(Room)\
        .join(Participant1, Room.participants)\
        .join(Participant2, Room.participants)\
        .filter(
            Room.is_private == True,
            Participant1.user_id == current_user_id,
            Participant2.user_id == target_user_id
        ).first()

    if common_room:
        return room_schema.dump(common_room), 200

    # 4. TẠO PHÒNG MỚI (Nếu chưa có)
    try:
        new_room = Room(is_private=True)
        db.session.add(new_room)
        db.session.flush()

        p1 = Participant(user_id=current_user_id, room_id=new_room.id)
        p2 = Participant(user_id=target_user_id, room_id=new_room.id)
        
        db.session.add_all([p1, p2])
        db.session.commit()

        return room_schema.dump(new_room), 201
    except Exception as e:
        db.session.rollback()
        return {"message": f"Lỗi server: {str(e)}"}, 500
def get_room_messages(current_user_id, room_id, page=1, per_page=20):
    # Lấy lịch sử tin nhắn (có phân trang)

    # Kiểm tra quyền: User có trong phòng này không?
    is_participant = Participant.query.filter_by(
        user_id=current_user_id, 
        room_id=room_id
    ).first()

    if not is_participant:
        return {"message": "Bạn không có quyền xem phòng này"}, 403

    # Query tin nhắn, sắp xếp mới nhất trước
    pagination = Message.query.filter_by(room_id=room_id)\
        .order_by(Message.timestamp.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    messages = pagination.items
    
    # Đảo ngược lại list để hiển thị cũ -> mới trên giao diện (tùy chọn)
    messages.reverse()

    return {
        "messages": messages_schema.dump(messages),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page
    }, 200


def save_message(user_id, room_id, content):
    # Service: Lưu tin nhắn mới vào DB

    try:
        # 1. Kiểm tra user có trong phòng không (Bảo mật)
        is_participant = Participant.query.filter_by(
            user_id=user_id, 
            room_id=room_id
        ).first()
        
        if not is_participant:
            return None, "User không ở trong phòng này"

        # Tạo và lưu tin nhắn
        new_msg = Message(
            content=content,
            sender_id=user_id,
            room_id=room_id
        )
        db.session.add(new_msg)
        db.session.commit()
        db.session.refresh(new_msg)
        # Trả về JSON của tin nhắn vừa tạo
        return message_schema.dump(new_msg), None
        
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi lưu tin nhắn: {e}")
        return None, str(e)

ALLOWED_IMG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMG_EXTENSIONS

def upload_chat_file(file_obj, user_id):
    """
    Service: Xử lý upload ảnh chat
    Input: File object, User ID
    Output: (Data, Error Message, Status Code)
    """
    # 1. Validate file
    if file_obj.filename == '' or not allowed_file(file_obj.filename):
        return None, "File không hợp lệ hoặc định dạng không hỗ trợ", 400

    try:
        # 2. Tạo tên file an toàn
        # Format: chat_{user_id}_{filename_gốc}
        filename = secure_filename(f"chat_{user_id}_{file_obj.filename}")
        
        # 3. Đường dẫn lưu trữ
        upload_folder = os.path.join(current_app.root_path, 'static/uploads')
        os.makedirs(upload_folder, exist_ok=True) # Tạo thư mục nếu chưa có
        
        # 4. Lưu file
        file_path = os.path.join(upload_folder, filename)
        file_obj.save(file_path)
        
        # 5. Trả về URL
        return {"url": f"/static/uploads/{filename}"}, None, 200
        
    except Exception as e:
        print(f"Chat upload error: {e}")
        return None, f"Lỗi server: {str(e)}", 500

def create_group_chat(creator_id, group_name, member_ids):
    """
    Service: Tạo nhóm chat mới
    Input: creator_id (người tạo), group_name, member_ids (list các ID bạn bè được mời)
    """
    if not group_name:
        return {"message": "Tên nhóm không được để trống"}, 400
    
    if not member_ids or len(member_ids) == 0:
        return {"message": "Nhóm phải có ít nhất 1 thành viên khác"}, 400

    # Validate: Đảm bảo tất cả member_ids đều tồn tại
    members = User.query.filter(User.id.in_(member_ids)).all()
    if len(members) != len(member_ids):
         return {"message": "Một số người dùng không tồn tại"}, 404

    try:
        # 1. Tạo Phòng
        new_group = Room(
            name=group_name,
            is_private=False, # Đánh dấu là Group
            admin_id=creator_id
        )
        db.session.add(new_group)
        db.session.flush() # Để lấy ID phòng

        # 2. Thêm Người Tạo vào phòng (Admin)
        admin_part = Participant(user_id=creator_id, room_id=new_group.id)
        db.session.add(admin_part)

        # 3. Thêm Các Thành Viên vào phòng
        for mem_id in member_ids:
            # (Nâng cao: Nên kiểm tra xem mem_id có phải là bạn của creator_id không ở đây)
            participant = Participant(user_id=mem_id, room_id=new_group.id)
            db.session.add(participant)
        
        db.session.commit()

        return room_schema.dump(new_group), 201

    except Exception as e:
        db.session.rollback()
        return {"message": f"Lỗi server: {str(e)}"}, 500

def get_user_groups(user_id):
    """
    Lấy danh sách các nhóm chat mà user tham gia
    """
    try:
        groups = db.session.query(Room)\
            .join(Participant, Room.participants)\
            .filter(
                Participant.user_id == user_id,
                Room.is_private == False
            ).all()
            
        return rooms_schema.dump(groups), 200
    except Exception as e:
        return {"message": str(e)}, 500


def delete_group_chat(user_id, group_id):
    """
    Service: Xóa nhóm chat (Chỉ trưởng nhóm mới được xóa)
    """
    group = Room.query.get(group_id)
    
    if not group:
        return {"message": "Nhóm không tồn tại"}, 404
    
    if group.is_private:
        return {"message": "Không thể xóa cuộc trò chuyện cá nhân ở đây"}, 400
        
    # Kiểm tra quyền trưởng nhóm (Admin)
    if group.admin_id != user_id:
        return {"message": "Chỉ trưởng nhóm mới có quyền giải tán nhóm"}, 403

    try:
        # Xóa nhóm (Cascade sẽ tự xóa tin nhắn và participant nếu config đúng, 
        # nhưng an toàn nhất là xóa thủ công hoặc để SQLAlchemy lo)
        db.session.delete(group)
        db.session.commit()
        return {"message": "Đã giải tán nhóm", "id": group_id}, 200
        
    except Exception as e:
        db.session.rollback()
        return {"message": f"Lỗi server: {str(e)}"}, 500

def leave_group_chat(user_id, group_id):
    """
    Service: Người dùng tự rời khỏi nhóm
    """
    # 1. Kiểm tra xem có phải thành viên không
    participant = Participant.query.filter_by(user_id=user_id, room_id=group_id).first()
    
    if not participant:
        return {"message": "Bạn không phải thành viên nhóm này"}, 400

    try:
        # 2. Xóa participant
        db.session.delete(participant)
        
        # (Tùy chọn) Kiểm tra nếu nhóm không còn ai thì xóa nhóm luôn
        remaining = Participant.query.filter_by(room_id=group_id).count()
        if remaining == 0:
            group = Room.query.get(group_id)
            if group:
                db.session.delete(group)

        db.session.commit()
        return {"message": "Đã rời nhóm", "group_id": group_id}, 200
        
    except Exception as e:
        db.session.rollback()
        return {"message": f"Lỗi server: {str(e)}"}, 500