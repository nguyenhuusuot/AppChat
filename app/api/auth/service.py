from app import db
import re
from app.models.user import User
from app.schemas.user import user_schema
from flask_jwt_extended import create_access_token
import dns.resolver

# HÀM KIỂM TRA DOMAIN EMAIL
def check_email_domain(email):

    # Kiểm tra xem domain của email có thực sự tồn tại và có MX record không.
    
    try:
        domain = email.split('@')[1]
        # Tìm bản ghi MX (Mail Exchange) của domain
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
        # Domain không tồn tại hoặc không có mail server
        return False
    except Exception:
        # Các lỗi DNS khác (timeout, v.v.)
        return False

# HÀM KIỂM TRA BẢO MẬT 
def validate_security(username, password, email=None):
    # Username: Chỉ chữ thường và số
    if not re.match(r'^[a-z0-9]+$', username):
        return "Tên đăng nhập chỉ được chứa chữ thường (a-z) và số (0-9), không có khoảng trắng/kí tự đặc biệt."
    
    # Password: Min 9 ký tự, 1 hoa, 1 thường, 1 số, 1 đặc biệt
    pattern_pass = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{9,}$'
    if not re.match(pattern_pass, password):
        return "Mật khẩu phải có ít nhất 9 ký tự, bao gồm chữ hoa, chữ thường, số và ký tự đặc biệt (@$!%*?&)."

    # Email: Kiểm tra định dạng và Domain
    if email:
        # Check Regex trước 
        pattern_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern_email, email):
            return "Định dạng Email không hợp lệ."
        
        # Check MX Record sau
        if not check_email_domain(email):
            return "Tên miền Email không tồn tại hoặc không thể nhận thư."
    return None 

def register_user(data):
    username = data['username']
    password = data['password']
    email = data['email']

    # VALIDATE INPUT 
    error_msg = validate_security(username, password, email)
    if error_msg:
        return {"message": error_msg}, 400

    # CHECK TRÙNG 
    if User.query.filter_by(username=username).first():
        return {"message": "Username đã tồn tại"}, 409
    if User.query.filter_by(email=email).first():
        return {"message": "Email đã tồn tại"}, 409

    # TẠO USER 
    new_user = User(
        username=username,
        email=email,
        display_name=username 
    )
    new_user.set_password(password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"message": str(e)}, 500

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

    # Service lấy thông tin người dùng hiện tại qua ID
    user = User.query.get(user_id)
    
    if not user:
        return {"message": "Không tìm thấy người dùng"}, 404
    
    # Trả về thông tin user (đã ẩn password nhờ schema)
    return user_schema.dump(user), 200