from datetime import datetime, timezone
from app import db

class Room(db.Model):
    __tablename__ = 'room'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True) 
    name = db.Column(db.String(100), nullable=True) 
    avatar = db.Column(db.String(200), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_private = db.Column(db.Boolean, default=True) 
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  
    
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
    admin = db.relationship('User', foreign_keys=[admin_id])
    
    def __repr__(self):
        return f'<Room {self.id} (Private: {self.is_private})>'
