from app import db
import datetime

class Participant(db.Model):
    __tablename__ = 'participant'    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False) 
    # Thời điểm user tham gia phòng
    joined_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)   
    # Quan hệ ngược lại để truy cập dễ dàng
    user = db.relationship(
        'User', 
        back_populates='rooms'
    )
    room = db.relationship(
        'Room', 
        back_populates='participants'
    )
    # Đảm bảo một user chỉ có thể tham gia 1 phòng 1 lần
    __table_args__ = (db.UniqueConstraint('user_id', 'room_id', name='_user_room_uc'),)

    def __repr__(self):
        return f'<Participant User={self.user_id} Room={self.room_id}>'