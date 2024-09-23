import threading
from flask import Flask
from app.controllers.alert_controller import alert_blueprint 
from app.controllers.alert_controller import create_alert_blueprint 
from flask_cors import CORS
from app.models.alert_model import AlertModel
from app.socketio import socketio 
from app.services.monitor_service import monitor_storage
 
active_threads = 0
thread_lock = threading.Lock()

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Registramos los blueprints 
    alert_model = AlertModel()
    app.register_blueprint(create_alert_blueprint(alert_model))
 
    # Iniciamos socketio
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')

    def start_monitor_thread():
        global active_threads
        with thread_lock:
            if active_threads < 1:  
                active_threads += 1
                monitor_storage(alert_model)
                active_threads -= 1
 
    # Iniciamos el hilo de monitoreo
    monitor_thread = threading.Thread(target=start_monitor_thread)
    monitor_thread.daemon = True
    monitor_thread.start() 
    return app
