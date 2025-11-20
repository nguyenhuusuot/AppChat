import json
import pytest

def test_register_user(client):
    # Test đăng ký thành công
    payload = {
        'username': 'testuser',
        'email': 'test@gmail.com',
        'password': 'Password123@' # Pass mạnh để qua validate
    }
    
    response = client.post('/api/auth/register', json=payload)
    
    # DEBUG: Nếu lỗi, in ra message từ server để biết nguyên nhân
    if response.status_code != 201:
        print(f"\n[DEBUG] Register Error: {response.json}")

    assert response.status_code == 201
    assert 'username' in response.json

def test_login_user(client):
    # Đăng ký trước (để có user trong DB test)
    reg_payload = {
        'username': 'loginuser',
        'email': 'login@gmail.com',
        'password': 'Password123@'
    }
    client.post('/api/auth/register', json=reg_payload)

    # Đăng nhập
    login_payload = {
        'username': 'loginuser',
        'password': 'Password123@'
    }
    response = client.post('/api/auth/login', json=login_payload)
    
    if response.status_code != 200:
        print(f"\n[DEBUG] Login Error: {response.json}")

    assert response.status_code == 200
    data = response.json
    assert 'access_token' in data