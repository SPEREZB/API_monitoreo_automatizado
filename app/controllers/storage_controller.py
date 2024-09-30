from flask import Blueprint, jsonify, request
from app.services.storage_service import StorageService

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

@storage_blueprint.route('/api/data/balance', methods=['POST'])
def balance_storage():
    """Balancea los datos entre discos y dispositivos de almacenamiento."""
    demand = request.json.get('demand')
    balance_result = data_service.balance_storage(demand)
    return jsonify(balance_result)