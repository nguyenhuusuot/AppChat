import os
from flask import current_app
from app import db
from app.models.user import User, friendship 
from app.schemas.user import users_schema,user_schema
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, and_
from werkzeug.utils import secure_filename

def get_friends(current_user_id):
    """
    Service: Lấy danh sách TẤT CẢ bạn bè (status='accepted')
    """
    try:
        # Tìm ID của những người mình gửi lời mời và đã được chấp nhận
        sent_query = db.session.query(friendship.c.friend_id).filter(
            friendship.c.user_id == current_user_id,
            friendship.c.status == 'accepted'
        )
        
        # Tìm ID của những người gửi lời mời cho mình và mình đã chấp nhận
        received_query = db.session.query(friendship.c.user_id).filter(
            friendship.c.friend_id == current_user_id,
            friendship.c.status == 'accepted'
        )
        
        # Kết hợp (UNION) hai danh sách ID đó lại
        friend_ids = sent_query.union(received_query).all()
        
        # Chuyển list các tuple (ví dụ: [(1,), (2,)]) thành list ID [1, 2]
        friend_id_list = [id[0] for id in friend_ids]
        
        # Lấy thông tin User từ danh sách ID
        friends = User.query.filter(User.id.in_(friend_id_list)).all()
        
        return users_schema.dump(friends), 200

    except Exception as e:
        return {"message": f"Lỗi server: {str(e)}"}, 500

def get_pending_requests(current_user_id):
    """
    Service: Lấy danh sách những người đã gửi lời mời cho mình
    """
    try:
        # Tìm ID của những người gửi lời mời cho mình và đang 'pending'
        sender_ids_query = db.session.query(friendship.c.user_id).filter(
            friendship.c.friend_id == current_user_id,
            friendship.c.status == 'pending'
        )
        
        sender_id_list = [id[0] for id in sender_ids_query.all()]
        
        # Lấy thông tin User của những người gửi
        pending_users = User.query.filter(User.id.in_(sender_id_list)).all()
        
        return users_schema.dump(pending_users), 200

    except Exception as e:
        return {"message": f"Lỗi server: {str(e)}"}, 500


def send_friend_request(current_user_id, target_user_id):
    """
    Service: gửi một lời mời kết bạn
    """
    # Không thể tự kết bạn với chính mình
    if current_user_id == target_user_id:
        return {"message": "Bạn không thể tự kết bạn với chính mình"}, 400
        
    # Kiểm tra xem user có tồn tại không
    target_user = User.query.get(target_user_id)
    if not target_user:
        return {"message": "Không tìm thấy user mục tiêu"}, 404
        
    # Kiểm tra xem đã tồn tại quan hệ (bất kỳ) chưa
    existing_relation = db.session.query(friendship).filter(
        or_(
            and_(friendship.c.user_id == current_user_id, friendship.c.friend_id == target_user_id),
            and_(friendship.c.user_id == target_user_id, friendship.c.friend_id == current_user_id)
        )
    ).first()
    
    if existing_relation:
        return {"message": f"Đã tồn tại quan hệ với status: {existing_relation.status}"}, 409
        
    # Tạo lời mời
    try:
        stmt = friendship.insert().values(
            user_id=current_user_id,
            friend_id=target_user_id,
            status='pending'
        )
        db.session.execute(stmt)
        db.session.commit()
        return {"message": "Đã gửi lời mời kết bạn"}, 201
        
    except IntegrityError:
        db.session.rollback()
        return {"message": "Lỗi Database: Không thể gửi lời mời"}, 500
    except Exception as e:
        db.session.rollback()
        return {"message": f"Lỗi server: {str(e)}"}, 500

def accept_friend_request(current_user_id, sender_user_id):
    """
    Service: Chấp nhận một lời mời kết bạn
    """
    try:
        # Cập nhật record 'friendship'
        stmt = friendship.update().where(
            and_(
                friendship.c.user_id == sender_user_id,      # Người gửi
                friendship.c.friend_id == current_user_id, # Người nhận (là mình)
                friendship.c.status == 'pending'           # Phải đang chờ
            )
        ).values(status='accepted') # Đổi status

        result = db.session.execute(stmt)
        db.session.commit()
        
        # result.rowcount cho biết bao nhiêu hàng đã bị ảnh hưởng
        if result.rowcount == 0:
            return {"message": "Không tìm thấy lời mời kết bạn nào"}, 404
            
        return {"message": "Đã chấp nhận kết bạn"}, 200
        
    except Exception as e:
        db.session.rollback()
        return {"message": f"Lỗi server: {str(e)}"}, 500
# Cấu hình file ảnh hợp lệ
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_user_avatar(user_id, file_obj):
    """
    Service: Xử lý logic lưu file ảnh và cập nhật DB
    """
    # 1. Validate file
    if file_obj.filename == '' or not allowed_file(file_obj.filename):
        return None, "File không hợp lệ hoặc sai định dạng", 400

    try:
        # 2. Xử lý tên file an toàn
        # Đặt tên theo format: user_{id}_{filename} để tránh trùng
        filename = secure_filename(f"user_{user_id}_{file_obj.filename}")
        
        # 3. Xác định đường dẫn lưu (static/uploads)
        upload_folder = os.path.join(current_app.root_path, 'static/uploads')
        os.makedirs(upload_folder, exist_ok=True) # Tạo thư mục nếu chưa có
        
        # 4. Lưu file vật lý vào ổ cứng
        file_path = os.path.join(upload_folder, filename)
        file_obj.save(file_path)
        
        # 5. Cập nhật tên file vào Database
        user = User.query.get(user_id)
        if user:
            user.avatar = filename
            db.session.commit()
            
            # Trả về đường dẫn URL để frontend hiển thị
            return {"avatar_url": filename}, None, 200
        else:
             return None, "User không tồn tại", 404

    except Exception as e:
        print(f"Lỗi upload: {e}")
        return None, f"Lỗi server: {str(e)}", 500

def search_users_by_query(query_text, current_user_id): # <--- Thêm tham số current_user_id
    """
    Service: Tìm kiếm user (Loại bỏ chính mình)
    """
    if not query_text:
        return [], None, 200
        
    try:
        users = User.query.filter(
            and_(
                or_(
                    User.username.ilike(f"%{query_text}%"), 
                    User.email.ilike(f"%{query_text}%")
                ),
                User.id != current_user_id # <--- Loại bỏ chính mình
            )
        ).limit(10).all()
        
        return users_schema.dump(users), None, 200
    except Exception as e:
        return None, f"Lỗi server: {str(e)}", 500

def cancel_friend_request(current_user_id, target_user_id):
    """
    Service: Hủy lời mời kết bạn (hoặc hủy kết bạn)
    """
    try:
        # Tìm mối quan hệ bất kể trạng thái (pending hoặc accepted)
        relation = db.session.query(friendship).filter(
            or_(
                and_(friendship.c.user_id == current_user_id, friendship.c.friend_id == target_user_id),
                and_(friendship.c.user_id == target_user_id, friendship.c.friend_id == current_user_id)
            )
        ).first() # Friendship là bảng, không phải model, nên trả về Row

        if not relation:
            return {"message": "Không tìm thấy quan hệ để hủy"}, 404

        # Xóa record khỏi bảng friendship
        stmt = friendship.delete().where(
            or_(
                and_(friendship.c.user_id == current_user_id, friendship.c.friend_id == target_user_id),
                and_(friendship.c.user_id == target_user_id, friendship.c.friend_id == current_user_id)
            )
        )
        db.session.execute(stmt)
        db.session.commit()
        
        return {"message": "Đã hủy kết bạn/lời mời"}, 200

    except Exception as e:
        db.session.rollback()
        return {"message": f"Lỗi server: {str(e)}"}, 500
    
def update_user_profile(user_id, data):
    """
    Service: Cập nhật thông tin cá nhân (Username, Email...)
    """
    user = User.query.get(user_id)
    if not user:
        return {"message": "User không tồn tại"}, 404

    # Lấy dữ liệu mới
    new_username = data.get('username')
    new_email = data.get('email')

    # Validate cơ bản
    if not new_username or not new_email:
        return {"message": "Username và Email không được để trống"}, 400

    # Kiểm tra trùng lặp (Nếu đổi tên khác tên cũ)
    if new_username != user.username:
        if User.query.filter_by(username=new_username).first():
             return {"message": "Username này đã có người dùng"}, 409
    
    if new_email != user.email:
        if User.query.filter_by(email=new_email).first():
             return {"message": "Email này đã có người dùng"}, 409

    try:
        # Cập nhật
        user.username = new_username
        user.email = new_email
        db.session.commit()
        
        return users_schema.dump(user), 200
    except Exception as e:
        db.session.rollback()
        return {"message": f"Lỗi server: {str(e)}"}, 500