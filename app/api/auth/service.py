from app import db
from app.models.user import User
from app.schemas.user import user_schema
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import create_access_token


def register_user(data):
    """
    Service để xử lý logic đăng ký user
    """
    if User.query.filter_by(username=data['username']).first():
        return {"message": "Username already exists"}, 409
    
    if User.query.filter_by(email=data['email']).first():
        return {"message": "Email already exists"}, 409

    # Tạo user object
    new_user = User(
        username=data['username'],
        email=data['email']
    )
    new_user.set_password(data['password'])
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
    except IntegrityError: 
        db.session.rollback()
        return {"message": "Lỗi Database: User hoặc Email đã tồn tại"}, 409
        
    except Exception as e:
        db.session.rollback()
        return {"message": f"Một lỗi server đã xảy ra: {str(e)}"}, 500

    # Trả về thành công
    return user_schema.dump(new_user), 201

def login_user(data):
    # Service để xử lý logic đăng nhập
    username = data.get('username')
    password = data.get('password')
    # Tìm user
    user = User.query.filter_by(username=username).first()
    # Kiểm tra mật khẩu
    if not user or not user.check_password(password):
        return {"message":"Sai username hoặc password"},401
    
    # Tạo access token
    access_token = create_access_token(identity=str(user.id)) 

    return {"access_token":access_token},200

def get_me(user_id):
    """
    Service lấy thông tin người dùng hiện tại qua ID
    """
    user = User.query.get(user_id)
    
    if not user:
        return {"message": "Không tìm thấy người dùng"}, 404
    
    # Trả về thông tin user (đã ẩn password nhờ schema)
    return user_schema.dump(user), 200