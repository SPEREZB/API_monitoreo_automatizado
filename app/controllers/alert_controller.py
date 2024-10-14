import subprocess 
from flask import Blueprint, jsonify,request, jsonify
import psutil
from app.models.alert_model import AlertModel
from app.services.alert_service import AlertService 
import logging

alert_blueprint = Blueprint('alerts', __name__)
alert_model = AlertModel()
alert_service = AlertService()
 
logging.basicConfig(filename='system_monitor.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def create_alert_blueprint(model_instance):
    global alert_model
    alert_model = model_instance   

    return alert_blueprint  

@alert_blueprint.route('/api/report_alerts', methods=['GET'])
def get_all_alerts_errors():
    alerts= alert_service.get_alerts_errors()
    return jsonify(alerts=alerts)

@alert_blueprint.route('/api/removeDisk', methods=['POST'])
def remove_disk():
    """Remover disco."""
    disk = request.json.get('disk')
    adjustment_result = alert_service.remove_disk(alert_model,disk)
    return jsonify(adjustment_result)

@alert_blueprint.route('/api/identified_alerts', methods=['GET'])
def get_check_identified_errors():
    state= alert_service.check_identified_errors()
    return jsonify(state=state)


@alert_blueprint.route('/api/get_devices', methods=['GET'])
def get_devices():
    devices = []
    smartctl_devices = []

    try:
        # Ejecutar el comando `smartctl --scan` para obtener los discos disponibles
        result = subprocess.run(['smartctl', '--scan'], capture_output=True, text=True, check=True)
 
        for line in result.stdout.splitlines():
            if line.startswith('/dev/'):
                device = line.split(' ')[0]   
                smartctl_devices.append(device)

        # Usamos psutil para obtener información sobre particiones montadas
        for part in psutil.disk_partitions(all=False):
            if 'rw' in part.opts:  
                usage = psutil.disk_usage(part.mountpoint)
 
                devices.append({
                    'filesystem': part.device,
                    'mountpoint': part.mountpoint,
                    'size': usage.total,
                    'used': usage.used,
                    'available': usage.free
                })

        alert_model.add_disk(devices)
     
        removed_disks = alert_model.get_removed_disk()
        for removed in removed_disks:
            if removed in devices:
                devices.remove(removed)
 
        return jsonify({
            'devices': devices,  
            'smartctl_devices': smartctl_devices  
        })

    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Error executing smartctl command', 'details': str(e)}), 500


@alert_blueprint.route('/api/choose_devices', methods=['POST'])
def choose_devices():
    try:
        data = request.get_json()
     
        device = data['name']
         
        alert_model.choose_disk(device)
        
        return jsonify({'message': 'Device chosen successfully'}), 200  

    except Exception as e: 
        return jsonify({'error': str(e)}), 500 