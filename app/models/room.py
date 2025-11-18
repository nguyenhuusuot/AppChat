from app import db
import datetime

class Room(db.Model):
    __tablename__ = 'room'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True) 
    is_private = db.Column(db.Boolean, default=True) 
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)   
    # Quan hệ với tin nhắn: Một Room có nhiều Message
    messages = db.relationship(
        'Message', 
        back_populates='room', 
        lazy='dynamic', 
        cascade="all, delete-orphan"
    )
    
    # Quan hệ với người tham gia (qua bảng Participant)
    participants = db.relationship(
        'Participant', 
        back_populates='room', 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f'<Room {self.id} (Private: {self.is_private})>'
