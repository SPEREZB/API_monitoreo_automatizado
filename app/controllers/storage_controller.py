from flask import Blueprint, jsonify, request
from app.services.storage_service import StorageService
import os
import shutil

storage_blueprint = Blueprint('volumen', __name__)
data_service = StorageService()

@storage_blueprint.route('/api/data', methods=['GET'])
def get_data():
    """Obtiene los datos almacenados y su capacidad."""
    data_info = data_service.get_storage_info()
    return jsonify(data_info)

@storage_blueprint.route('/api/data/adjust', methods=['POST'])
def adjust_storage():
    """Ajusta la capacidad de almacenamiento según la demanda."""
    demand = request.json.get('demand')
    adjustment_result = data_service.adjust_storage(demand)
    return jsonify(adjustment_result)

@storage_blueprint.route('/api/data/liberar', methods=['POST'])
def liberar_storage():
    """Liberar espacio.""" 
    ruta = request.json.get('ruta')
    space = data_service.liberar_space(ruta)
    return jsonify(space)

@storage_blueprint.route('/api/data/balance', methods=['POST'])
def balance_storage():
    """Balancea los archivos entre discos y dispositivos de almacenamiento."""
    try:
        disks = request.json.get('disk')
        if not disks:
            return jsonify({'status': 'Error', 'message': 'No se enviaron datos de discos'}), 400
        
        # Llamar al servicio para balancear discos
        balanced_disks = data_service.balance_disks_2(disks)
        
        return jsonify({'status': 'Balance completado', 'disks': balanced_disks})

    except Exception as e:
        return jsonify({'status': 'Error al balancear', 'error': str(e)})

 