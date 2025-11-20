import os
from werkzeug.utils import secure_filename
from flask import current_app
from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased
from app import db
from app.models.room import Room
from app.models.participant import Participant
from app.models.message import Message
from app.models.user import User, friendship
from app.schemas.message import room_schema, rooms_schema, messages_schema, message_schema

# LOGIC UPLOAD ẢNH CHAT

ALLOWED_IMG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMG_EXTENSIONS

def upload_chat_file(file_obj, user_id):
    if file_obj.filename == '' or not allowed_file(file_obj.filename):
        return None, "File không hợp lệ hoặc định dạng không hỗ trợ", 400

    try:
        filename = secure_filename(f"chat_{user_id}_{file_obj.filename}")
        upload_folder = os.path.join(current_app.root_path, 'static/uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file_obj.save(file_path)
        
        return {"url": f"/static/uploads/{filename}"}, None, 200
        
    except Exception as e:
        print(f"Chat upload error: {e}")
        return None, f"Lỗi server: {str(e)}", 500


# LOGIC QUẢN LÝ PHÒNG CHAT

def get_or_create_private_room(current_user_id, target_user_id):
    # Validate cơ bản
    if current_user_id == target_user_id:
        return {"message": "Không thể chat với chính mình"}, 400

    if not User.query.get(target_user_id):
        return {"message": "Người dùng không tồn tại"}, 404

    # Kiểm tra quan hệ bạn bè
    is_friend = db.session.query(friendship).filter(
        or_(
            and_(friendship.c.user_id == current_user_id, friendship.c.friend_id == target_user_id, friendship.c.status == 'accepted'),
            and_(friendship.c.user_id == target_user_id, friendship.c.friend_id == current_user_id, friendship.c.status == 'accepted')
        )
    ).first()

    if not is_friend:
        return {"message": "Hai người chưa là bạn bè, không thể nhắn tin."}, 403

    # Tìm phòng tồn tại
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

    # Tạo mới
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

# HÀM TẠO NHÓM
def create_group_chat(creator_id, group_name, member_ids):
    # Tạo nhóm chat mới
    # Yêu cầu: Có tên nhóm và tối thiểu 3 thành viên (Creator + 2 người khác)

    if not group_name:
        return {"message": "Tên nhóm không được để trống"}, 400
    
    if not member_ids or len(member_ids) < 2:
        return {"message": "Nhóm phải có tối thiểu 3 thành viên (Bạn và ít nhất 2 người khác)"}, 400

    # Loại bỏ creator_id khỏi danh sách member_ids nếu frontend lỡ gửi lên (để tránh trùng)
    members_to_add = [uid for uid in member_ids if uid != creator_id]

    # Validate user tồn tại
    valid_members = User.query.filter(User.id.in_(members_to_add)).all()
    if len(valid_members) < 2:
         return {"message": "Không đủ thành viên hợp lệ để tạo nhóm"}, 400

    try:
        # Tạo Phòng với admin_id là người tạo
        new_group = Room(
            name=group_name,
            is_private=False,
            admin_id=creator_id # Xác định Trưởng nhóm
        )
        db.session.add(new_group)
        db.session.flush()

        # Tạo danh sách tham gia (Bao gồm cả Trưởng nhóm)
        participants = []
        
        # Thêm Trưởng nhóm
        participants.append(Participant(user_id=creator_id, room_id=new_group.id))
        
        # Thêm các thành viên khác
        for mem in valid_members:
            participants.append(Participant(user_id=mem.id, room_id=new_group.id))
            
        db.session.add_all(participants)
        db.session.commit()

        return room_schema.dump(new_group), 201

    except Exception as e:
        db.session.rollback()
        return {"message": f"Lỗi server: {str(e)}"}, 500

def get_user_groups(user_id):
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
    # Xóa nhóm chat (Chỉ trưởng nhóm mới được xóa)
    group = Room.query.get(group_id)
    
    if not group:
        return {"message": "Nhóm không tồn tại"}, 404
    
    if group.is_private:
        return {"message": "Không thể xóa cuộc trò chuyện cá nhân ở đây"}, 400
        
    # Kiểm tra quyền trưởng nhóm
    if group.admin_id != user_id:
        return {"message": "Chỉ trưởng nhóm mới có quyền giải tán nhóm"}, 403

    try:
        db.session.delete(group)
        db.session.commit()
        return {"message": "Đã giải tán nhóm", "id": group_id}, 200
        
    except Exception as e:
        db.session.rollback()
        return {"message": f"Lỗi server: {str(e)}"}, 500

def leave_group_chat(user_id, group_id):
    participant = Participant.query.filter_by(user_id=user_id, room_id=group_id).first()
    
    if not participant:
        return {"message": "Bạn không phải thành viên nhóm này"}, 400

    try:
        db.session.delete(participant)
        
        # Nếu nhóm không còn ai -> Xóa nhóm
        remaining = Participant.query.filter_by(room_id=group_id).count()
        if remaining == 0:
            group = Room.query.get(group_id)
            if group: db.session.delete(group)

        db.session.commit()
        return {"message": "Đã rời nhóm", "group_id": group_id}, 200
        
    except Exception as e:
        db.session.rollback()
        return {"message": f"Lỗi server: {str(e)}"}, 500


# 3. LOGIC TIN NHẮN

def get_room_messages(current_user_id, room_id, page=1, per_page=20):
    is_participant = Participant.query.filter_by(
        user_id=current_user_id, 
        room_id=room_id
    ).first()

    if not is_participant:
        return {"message": "Bạn không có quyền xem phòng này"}, 403

    pagination = Message.query.filter_by(room_id=room_id)\
        .order_by(Message.timestamp.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    results = pagination.items
    results.reverse()

    return {
        "messages": messages_schema.dump(results),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page
    }, 200

def save_message(user_id, room_id, content):
    try:
        is_participant = Participant.query.filter_by(
            user_id=user_id, 
            room_id=room_id
        ).first()
        
        if not is_participant:
            return None, "User không ở trong phòng này"

        new_msg = Message(
            content=content,
            sender_id=user_id,
            room_id=room_id
        )
        db.session.add(new_msg)
        db.session.commit()
        
        db.session.refresh(new_msg)
        
        return message_schema.dump(new_msg), None
        
    except Exception as e:
        db.session.rollback()
        return None, str(e)