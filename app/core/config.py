import os
from dotenv import load_dotenv
# tìm đường dẫn dự án
basedir = os.path.abspath(os.path.dirname(__file__))
# tải biến môi trường
load_dotenv(os.path.join(basedir,'.env'))

class Config:
    # Cấu hình cơ sở
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'key_bao_mat_2'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt_key_bao_mat2'
    # Cấu hình sqlaichemy 
    SQLALCHEMY_TRACK_MODIFICATIONS =False
    # Cấu hình redis cho socketio
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
class DevelopmentConfig(Config):
    # Cấu hình môi trường phát triển
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app-dev-db')

class ProductionConfig(Config):
    # Cấu hình cho môi trường sản phẩm 
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class TestingConfig(Config):
    # Cấu hình cho môi trường kiểm thử
    TESTING = True
    DEBUG = True
    # Dùng database riêng cho testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Tắt jwt hoặc dùng key khác
    JWT_SECRET_KEY = 'test_secret_key'

# Dictionary để map tên môi trường (string) với Class Config tương ứng
config_by_name={
    'dev':DevelopmentConfig,
    'prod': ProductionConfig,
    'test': TestingConfig
}


def get_config_name():
    # Mặc định là dev
    return os.environ.get('FLASK_ENV','dev') 
