from app import ma
from app.models.room import Room
from app.models.message import Message
from app.models.participant import Participant
from app.schemas.user import UserSchema
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields

# Khai báo ParticipantSchema TRƯỚC (Vì RoomSchema cần dùng nó)
class ParticipantSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Participant
        load_instance = False
        include_fk = True # Để lấy room_id, user_id

    # Lồng thông tin User (để biết ai là ai trong phòng)
    user = fields.Nested(UserSchema(only=("id", "username", "email")))

# Khai báo MessageSchema (Cũng nên khai báo trước Room)
class MessageSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Message
        load_instance = False
        include_fk = True

    # Lồng thông tin người gửi
    sender = fields.Nested(UserSchema(only=("id", "username", "avatar"))) 

# Khai báo RoomSchema SAU CÙNG
class RoomSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Room
        load_instance = False
        include_fk = True

    participants = fields.Nested(ParticipantSchema, many=True)
    # Tin nhắn cuối cùng (để hiển thị preview)
    last_message = fields.Nested(MessageSchema, dump_only=True)
    admin = fields.Nested(UserSchema(only=("id", "username")), dump_only=True)


#  Khởi tạo instance
message_schema = MessageSchema()
messages_schema = MessageSchema(many=True)
room_schema = RoomSchema()
rooms_schema = RoomSchema(many=True)