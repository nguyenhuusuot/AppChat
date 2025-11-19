from app import db 
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

# Bảng trung gian cho quan hệ bạn bè (nhiều-nhiều)
friendship = db.Table('friendship',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('status', db.Enum('pending', 'accepted', name='friendship_status'), default='pending'),
    db.Column('created_at', db.DateTime, default=datetime.datetime.utcnow)
)

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    avatar = db.Column(db.String(200), default=None)
    # Quan hệ với tin nhắn: Một User có thể gửi nhiều Message
    messages_sent = db.relationship('Message', 
                                    back_populates='sender', 
                                    lazy='dynamic')

    # Quan hệ với phòng chat (qua bảng Participant)
    rooms = db.relationship('Participant', back_populates='user')

    # Quan hệ bạn bè (nhiều-nhiều, tự tham chiếu)
    # Phần xử lý logic bạn bè
    friends = db.relationship(
        'User', 
        secondary=friendship,
        primaryjoin=(friendship.c.user_id == id), # Ai là người gửi lời mời
        secondaryjoin=(friendship.c.friend_id == id), # Ai là người nhận
        backref=db.backref('friend_of', lazy='dynamic'), # Ai đã kết bạn với tôi
        lazy='dynamic'
    )

    def __repr__(self):
        return f'<User {self.username}>'

    # Phương thức helper để băm mật khẩu
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Phương thức helper để kiểm tra mật khẩu
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Các phương thức helper cho logic kết bạn
    def add_friend(self, user):
        if not self.is_friend(user):
            # Tạo quan hệ pending
            pass 
            
    def is_friend(self, user):
        # Kiểm tra xem đã là bạn bè (status='accepted') chưa
        is_friend = self.friends.filter(
            friendship.c.friend_id == user.id,
            friendship.c.status == 'accepted'
        ).count() > 0
        
        is_friend_of = self.friend_of.filter(
            friendship.c.user_id == user.id,
            friendship.c.status == 'accepted'
        ).count() > 0
        
        return is_friend or is_friend_of