import threading
from time import sleep
from flask import Flask
from app.controllers.alert_controller import create_alert_blueprint 
from app.controllers.storage_controller import storage_blueprint 
from flask_cors import CORS
from app.models.alert_model import AlertModel
from app.socketio import socketio 
from app.services.alert_service import AlertService
 
active_threads = 0
thread_lock = threading.Lock()
alert_service= AlertService()

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Registramos los blueprints 
    alert_model = AlertModel()
    app.register_blueprint(create_alert_blueprint(alert_model))
    app.register_blueprint(storage_blueprint)
 
    # Iniciamos socketio
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')

    def start_monitor_thread():
        global active_threads
        with thread_lock:
            if active_threads == 0:
                active_threads += 1
                alert_service.monitor_storage(alert_model) 
                active_threads -= 1
 
    # Iniciamos el hilo de monitoreo
    monitor_thread = threading.Thread(target=start_monitor_thread)
    monitor_thread.daemon = True
    monitor_thread.start() 
    return app
