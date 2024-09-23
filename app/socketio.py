from flask_socketio import SocketIO

# Especificar el controlador asíncrono importante
socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent')
