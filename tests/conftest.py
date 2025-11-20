import pytest
from app import create_app, db

@pytest.fixture
def app():
    # Khởi tạo app với config 'test'
    app = create_app('test')
    
    # Tạo context và database
    with app.app_context():
        db.create_all() # Tạo bảng
        yield app
        db.session.remove()
        db.drop_all() # Xóa bảng sau khi test

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()