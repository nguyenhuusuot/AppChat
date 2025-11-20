from gevent import monkey
monkey.patch_all()

import os     
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

from app import create_app,socketio
from app.core.config import get_config_name

# Lấy tên config 
config_name = get_config_name()

# Tạo app instance
app = create_app(config_name)


if __name__ == '__main__':
    print(f"Starting server in  '{config_name}' mode..." )
    socketio.run(app, host='0.0.0.0', port=5000, debug=app.config['DEBUG'])