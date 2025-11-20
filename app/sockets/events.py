from flask import request
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token
from app import socketio
from app.api.chat import service as chat_service

# BỘ NHỚ TẠM
# online_users lưu user_id (int)
online_users = set()       
sid_to_user = {}           

# Xác thực Token 
def get_user_from_token():
    try:
        token = request.args.get('token') 
        if not token:
             token = request.headers.get('Authorization')
        
        if not token:
            return None
            
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
            
        decoded = decode_token(token)
        return int(decoded['sub'])
    except Exception as e:
        print(f"Socket Auth Error: {e}")
        return None

# CONNECT 
@socketio.on('connect')
def handle_connect():
    user_id = get_user_from_token()
    if not user_id:
        print(f"Client {request.sid} kết nối thất bại: Token lỗi")
        disconnect()
        return

    # Lưu mapping SID -> UserID
    sid_to_user[request.sid] = user_id
    
    # Thêm vào danh sách Online
    online_users.add(user_id)
    
    # Join phòng riêng
    join_room(str(user_id))
    
    print(f" User {user_id} đã kết nối (SID: {request.sid})")

    # Báo cho cả thế giới biết mình Online
    emit('user_status', {'user_id': user_id, 'status': 'online'}, broadcast=True)
    
    # Gửi danh sách những người ĐANG online cho chính mình
    # Để mình biết ai đang sáng đèn
    emit('online_list', list(online_users))

# DISCONNECT
@socketio.on('disconnect')
def handle_disconnect():
    user_id = sid_to_user.get(request.sid)
    
    if user_id:
        print(f"User {user_id} đã thoát (SID: {request.sid})")
        del sid_to_user[request.sid]
        
        # Kiểm tra xem User còn tab nào khác không
        if user_id not in sid_to_user.values():
            online_users.discard(user_id)
            # Báo Offline
            emit('user_status', {'user_id': user_id, 'status': 'offline'}, broadcast=True)

# JOIN ROOM 
@socketio.on('join')
def on_join(data):
    if isinstance(data, str):
        import json
        try: data = json.loads(data)
        except: return

    user_id = sid_to_user.get(request.sid)
    room_id = data.get('room_id')
    
    if user_id and room_id:
        # Ép kiểu string cho chắc chắn
        join_room(str(room_id))
        print(f"User {user_id} đã JOIN phòng {room_id}")

# SEND MESSAGE 
@socketio.on('send_message')
def on_send_message(data):
    # Xử lý data
    if isinstance(data, str):
        import json
        try: data = json.loads(data)
        except: return

    user_id = sid_to_user.get(request.sid)
    if not user_id: 
        print("Lỗi: Không tìm thấy user_id từ SID")
        return
    
    room_id = data.get('room_id')
    content = data.get('content')
    
    if not room_id or not content: return

    print(f"📩 User {user_id} gửi tin vào phòng {room_id}: {content}")

    # Lưu DB
    msg_json, error = chat_service.save_message(user_id, room_id, content)
    
    if error:
        emit('error', {'msg': error})
        return

    # Gửi tin nhắn cho mọi người trong phòng
    emit('new_message', msg_json, to=str(room_id))

@socketio.on('typing')
def on_typing(data):
    # Khi Client gửi 'typing', Server chuyển tiếp cho mọi người trong phòng (trừ người gửi)

    if isinstance(data, str):
        import json
        try: data = json.loads(data)
        except: return

    user_id = sid_to_user.get(request.sid)
    room_id = data.get('room_id')
    
    if user_id and room_id:
        # include_self=False: Không gửi lại cho chính mình
        emit('typing', {'user_id': user_id, 'room_id': room_id}, to=str(room_id), include_self=False)

@socketio.on('stop_typing')
def on_stop_typing(data):
    # Khi Client gửi 'stop_typing'

    if isinstance(data, str):
        import json
        try: data = json.loads(data)
        except: return

    user_id = sid_to_user.get(request.sid)
    room_id = data.get('room_id')
    
    if user_id and room_id:
        emit('stop_typing', {'user_id': user_id, 'room_id': room_id}, to=str(room_id), include_self=False)