import os
from werkzeug.utils import secure_filename
from flask import current_app
from sqlalchemy import or_, and_, delete 
from app import db
from app.models.user import User, friendship
from app.schemas.user import users_schema, user_schema
import re
import dns.resolver


# LOGIC UPLOAD & FILE
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_user_avatar(user_id, file_obj):
    if file_obj.filename == '' or not allowed_file(file_obj.filename):
        return None, "File không hợp lệ", 400
    try:
        filename = secure_filename(f"user_{user_id}_{file_obj.filename}")
        upload_folder = os.path.join(current_app.root_path, 'static/uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file_obj.save(file_path)
        
        user = User.query.get(user_id)
        if user:
            user.avatar = filename
            db.session.commit()
            return {"avatar_url": filename}, None, 200
        else: return None, "User không tồn tại", 404
    except Exception as e: return None, f"Lỗi server: {str(e)}", 500


# 2. LOGIC BẠN BÈ & TÌM KIẾM
def get_friends(current_user_id):
    try:
        sent_query = db.session.query(friendship.c.friend_id).filter(friendship.c.user_id == current_user_id, friendship.c.status == 'accepted')
        received_query = db.session.query(friendship.c.user_id).filter(friendship.c.friend_id == current_user_id, friendship.c.status == 'accepted')
        friend_ids = sent_query.union(received_query).all()
        friend_id_list = [id[0] for id in friend_ids]
        friends = User.query.filter(User.id.in_(friend_id_list)).all()
        return users_schema.dump(friends), 200
    except Exception as e: return {"message": str(e)}, 500

def get_pending_requests(current_user_id):
    try:
        sender_ids_query = db.session.query(friendship.c.user_id).filter(friendship.c.friend_id == current_user_id, friendship.c.status == 'pending')
        sender_id_list = [id[0] for id in sender_ids_query.all()]
        pending_users = User.query.filter(User.id.in_(sender_id_list)).all()
        return users_schema.dump(pending_users), 200
    except Exception as e: return {"message": str(e)}, 500

def send_friend_request(current_user_id, target_user_id):
    if current_user_id == target_user_id: return {"message": "Không thể tự kết bạn"}, 400
    if not User.query.get(target_user_id): return {"message": "User không tồn tại"}, 404
    
    existing = db.session.query(friendship).filter(
        or_(
            and_(friendship.c.user_id == current_user_id, friendship.c.friend_id == target_user_id),
            and_(friendship.c.user_id == target_user_id, friendship.c.friend_id == current_user_id)
        )
    ).first()
    
    if existing: return {"message": "Đã tồn tại quan hệ"}, 409

    try:
        stmt = friendship.insert().values(user_id=current_user_id, friend_id=target_user_id, status='pending')
        db.session.execute(stmt)
        db.session.commit()
        return {"message": "Đã gửi lời mời"}, 201
    except Exception as e: db.session.rollback(); return {"message": str(e)}, 500

def accept_friend_request(current_user_id, sender_user_id):
    try:
        stmt = friendship.update().where(
            and_(friendship.c.user_id == sender_user_id, friendship.c.friend_id == current_user_id, friendship.c.status == 'pending')
        ).values(status='accepted')
        
        result = db.session.execute(stmt)
        db.session.commit()
        
        if result.rowcount == 0: return {"message": "Lỗi hoặc không tìm thấy lời mời"}, 404
        return {"message": "Đã chấp nhận"}, 200
    except Exception as e: db.session.rollback(); return {"message": str(e)}, 500

# HÀM HỦY KẾT BẠN 
def cancel_friend_request(current_user_id, target_user_id):
    print(f"[SERVICE] Bắt đầu xóa quan hệ {current_user_id} <-> {target_user_id}")
    try:
        stmt = delete(friendship).where(
            or_(
                and_(friendship.c.user_id == current_user_id, friendship.c.friend_id == target_user_id),
                and_(friendship.c.user_id == target_user_id, friendship.c.friend_id == current_user_id)
            )
        )
        result = db.session.execute(stmt)
        db.session.commit()
        
        print(f"[SERVICE] Số dòng bị xóa: {result.rowcount}")

        if result.rowcount > 0:
            return {"message": "Đã hủy thành công"}, 200
        else:
            return {"message": "Không tìm thấy quan hệ để xóa"}, 404
            
    except Exception as e:
        db.session.rollback()
        print(f"[SERVICE ERROR]: {e}")
        return {"message": str(e)}, 500


def search_users_by_query(query_text, current_user_id):
    if not query_text: return [], None, 200
    try:
        search_conditions = [
            User.username.ilike(f"%{query_text}%"),
            User.display_name.ilike(f"%{query_text}%")
        ]
        if '@' in query_text:
            search_conditions.append(User.email.ilike(f"%{query_text}%"))

        users = User.query.filter(
            and_(
                or_(*search_conditions),
                User.id != current_user_id 
            )
        ).limit(10).all()
        
        users_data = users_schema.dump(users)

        for u_data in users_data:
            target_id = u_data['id']
            rel = db.session.query(friendship).filter(
                or_(
                    and_(friendship.c.user_id == current_user_id, friendship.c.friend_id == target_id),
                    and_(friendship.c.user_id == target_id, friendship.c.friend_id == current_user_id)
                )
            ).first()

            if not rel:
                u_data['friend_status'] = 'none'
            elif rel.status == 'accepted':
                u_data['friend_status'] = 'friend'
            elif rel.status == 'pending':
                if rel.user_id == current_user_id:
                    u_data['friend_status'] = 'sent'
                else:
                    u_data['friend_status'] = 'received'

        return users_data, None, 200
    except Exception as e:
        return None, str(e), 500

# LOGIC PROFILE

def check_email_domain(email):
    try:
        domain = email.split('@')[1]
        dns.resolver.resolve(domain, 'MX')
        return True
    except: return False

def update_user_profile(user_id, data):
    user = User.query.get(user_id)
    if not user: return {"message": "User không tồn tại"}, 404

    current_password = data.get('current_password')
    new_display_name = data.get('display_name')
    new_password = data.get('new_password')
    new_email = data.get('email') 

    if not current_password: return {"message": "Vui lòng nhập mật khẩu hiện tại"}, 400
    if not user.check_password(current_password): return {"message": "Mật khẩu hiện tại không đúng"}, 401

    if new_display_name: user.display_name = new_display_name

    if new_email and new_email != user.email:
        pattern_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern_email, new_email): return {"message": "Email không hợp lệ"}, 400
        if not check_email_domain(new_email): return {"message": "Tên miền Email không tồn tại"}, 400
        if User.query.filter_by(email=new_email).first(): return {"message": "Email này đã được sử dụng"}, 409
        user.email = new_email

    if new_password:
        if user.check_password(new_password): return {"message": "Mật khẩu mới phải khác mật khẩu cũ"}, 400
        pattern_pass = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{9,}$'
        if not re.match(pattern_pass, new_password): return {"message": "Mật khẩu mới không đủ mạnh"}, 400
        user.set_password(new_password)

    try:
        db.session.commit()
        return user_schema.dump(user), 200
    except Exception as e:
        db.session.rollback()
        return {"message": f"Lỗi server: {str(e)}"}, 500