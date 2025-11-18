from app import ma
from app.models.room import Room
from app.schemas.user import UserSchema    
from app.schemas.message import MessageSchema 
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields

class RoomSchema(SQLAlchemyAutoSchema):
    """
    Schema cho Phòng chat.
    Dùng để trả về danh sách các phòng và chi tiết phòng.
    """
    class Meta:
        model = Room
        load_instance = True
        include_fk = False 


    #    Trả về danh sách những người tham gia phòng này
    #    Dùng 'only' để chỉ lấy các trường cần thiết (tránh lộ email, v.v.)
    participants = fields.Nested(
        UserSchema(many=True, only=('id', 'username'))
    )
    
    #    Trả về tin nhắn cuối cùng trong phòng chat để hiển thị preview
    last_message = fields.Nested(MessageSchema(only=('content', 'timestamp', 'sender')))


# Khởi tạo cho API
room_schema = RoomSchema()    
rooms_schema = RoomSchema(many=True) 