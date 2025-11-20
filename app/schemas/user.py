from app import ma 
from app.models.user import User 
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields

class UserSchema(SQLAlchemyAutoSchema):
    # (Load) Xác thực dữ liệu đăng ký (username, email, password).
    # (Dump) Trả về thông tin user (ẩn password_hash).
    
    class Meta:
        model = User        
        load_instance = False  
        
    # Thêm các trường đặc biệt
    # id: Chỉ gửi ra (dump_only), không nhận vào
    id = ma.auto_field(dump_only=True) 
    # email: Bắt buộc phải có khi load
    email = ma.auto_field(required=True)
    # username: Bắt buộc phải có khi load
    username = ma.auto_field(required=True)
    # password_hash: Chỉ gửi ra (nhưng thực tế ta sẽ ẩn nó đi)
    password_hash = ma.auto_field(dump_only=True)
    # Thêm trường 'password' (không có trong DB)
    # Chỉ nhận vào (load_only), không bao giờ gửi ra
    password = fields.Str(required=True, load_only=True)
    display_name = fields.Str(dump_only=True) # Chỉ gửi xuống client
    # Trường ảo avatar url (để tiện hiển thị)
    avatar = fields.Str(dump_only=True)
# Khởi tạo các schema để dùng trong API
user_schema = UserSchema() 
users_schema = UserSchema(many=True) 