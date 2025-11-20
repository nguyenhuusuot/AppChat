from datetime import datetime, timezone
from app import db


class Message(db.Model):
    __tablename__ = 'message'   
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False) 
    # Trạng thái tin nhắn
    is_read = db.Column(db.Boolean, default=False) 

    sender = db.relationship(
        'User', 
        back_populates='messages_sent'
    )

    room = db.relationship(
        'Room', 
        back_populates='messages'
    )

    def __repr__(self):
        return f'<Message {self.id} from User {self.sender_id}>'
    
    

    # Helper để biến tin nhắn thành dictionary, dễ dàng gửi qua JSON/SocketIO
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() + 'Z', # Định dạng ISO 8601
            'sender': {
                'id': self.sender.id,
                'username': self.sender.username
            },
            'room_id': self.room_id,
            'is_read': self.is_read
        }