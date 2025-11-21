Một ứng dụng chat đơn giản được xây dựng bằng Python/Flask cho backend và Reacjs cho frontend — cho phép người dùng trò chuyện theo thời gian thực.
Deploy Render : https://frontend-appchat.onrender.com/
TK : test1, test2
MK : Test1@gmail, Test2@gmail

## Mô tả
AppChat cho phép:
- Người dùng đăng nhập/đăng ký (nếu có) và tham gia phòng chat  
- Gửi và nhận tin nhắn theo thời gian thực  
- Quản lý phòng chat, thành viên (nếu có)  
- Có cấu trúc chuẩn cho backend + frontend, dễ mở rộng.

## Công nghệ sử dụng  
- Flask (hoặc tương đương)  
- WebSockets (Socket.IO hoặc tương đương) để hỗ trợ realtime  
- Cơ sở dữ liệu PostgreSQL 
- Thư viện ngoài (xem `requirements.txt`)  
## Hướng dẫn khởi động
1. Clone repo:
   git clone https://github.com/nguyenhuusuot/AppChat.git
   cd AppChat
Tạo môi trường ảo và kích hoạt:
  python3 -m venv venv
  source venv/bin/activate    # trên Linux/Mac  
  # hoặc venv\Scripts\activate trên Windows
  
Cài các thư viện phụ thuộc:
pip install -r requirements.txt
Thiết lập biến môi trường (ví dụ copy .env.example thành .env và điền thông tin):

SECRET_KEY=your_secret_key
DATABASE_URL=your_database_url
Chạy migration (nếu sử dụng):
flask db upgrade    
Khởi chạy ứng dụng:

python run.py
Sau đó mở trình duyệt và truy cập http://localhost:5000/ (hoặc port khác tuỳ cấu hình).

Tính năng
 Đăng nhập / Đăng ký người dùng

  Tham gia phòng chat / tạo nhóm chat mới

  Gửi và nhận tin nhắn theo thời gian thực

  Giao diện người dùng responsive, gửi hình ảnh/file
