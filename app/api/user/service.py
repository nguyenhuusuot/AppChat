from app import db
from app.models.user import User, friendship 
from app.schemas.user import users_schema 
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, and_

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