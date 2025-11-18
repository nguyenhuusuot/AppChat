# app/schemas/message_schema.py

from app import ma
from app.models.message import Message
from app.schemas.user import UserSchema 
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class MessageSchema(SQLAlchemyAutoSchema):
    """
    Schema cho tin nhắn.
    """
    class Meta:
        model = Message
        load_instance = True
        include_fk = True # Bao gồm cả foreign key (sender_id, room_id)

    # Khi dump tin nhắn, không chỉ muốn 'sender_id'
    # Muốn cả thông tin của người gửi.
    sender = ma.Nested(UserSchema(only=('id', 'username')))

# Khởi tạo cho API
message_schema = MessageSchema()
messages_schema = MessageSchema(many=True)