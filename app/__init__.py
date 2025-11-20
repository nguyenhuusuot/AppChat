from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from .core.config import config_by_name
from flask_cors import CORS
from app.core import config

# Khởi tạo extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()

# Khởi tạo socketio
socketio = SocketIO(async_mode='gevent', cors_allowed_origins="*")

def create_app(config_name = 'dev'):
    # Hàm tạo application 
    # Tạo app 
    app = Flask(__name__)
    # Tải cấu hình
    app.config.from_object(config_by_name[config_name])
    # Tạo extensions với app
    CORS(app, resources={
        r"/api/*":{ # Áp dụng cho các route bắt đầu bằng api
            "origins":config.ALLOWED_ORIGINS,
            "supports_credentials":True
        }
    })
    db.init_app(app)
    migrate.init_app(app,db)
    jwt.init_app(app)
    ma.init_app(app)
    if app.debug:
        print("Running in DEBUG mode: SocketIO will use local memory (No Redis)")
        socketio.init_app(app, cors_allowed_origins="*")
    else:
        print("Running in PRODUCTION mode: SocketIO using Redis Message Queue")
        socketio.init_app(app, message_queue=app.config['REDIS_URL'], cors_allowed_origins="*")

    from .models import user, room, message, participant
    


    # Đăng ký blueprint 
    from .api.auth.controller import auth_bp
    from .api.chat.controller import chat_bp
    from .api.user.controller import users_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(users_bp, url_prefix='/api/users')

    # Đăng ký register
    from .sockets import events

    @app.route('/health')
    def health_check():
        return "App is running"
    

    return app