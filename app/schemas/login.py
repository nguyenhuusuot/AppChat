from app import ma
from marshmallow import fields

class LoginSchema(ma.Schema):
    # Xác thực dữ liệu đăng nhập
    username = fields.Str(required=True)
    password = fields.Str(required=True)

login_schema = LoginSchema()
