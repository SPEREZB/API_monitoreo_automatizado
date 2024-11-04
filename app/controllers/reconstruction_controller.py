from flask import Blueprint, Flask, request, jsonify
from zfec import filefec
import os
from app.models.alert_model import AlertModel
from app.services.reconstruction_service import ReconstructionService


reconstruction_blueprint = Blueprint('reconstruction', __name__)
reconstruction = ReconstructionService()

alert_model = AlertModel()

@reconstruction_blueprint.route('/api/encode_disk', methods=['POST'])
def encode_disk():
    """Codifica el contenido de un disco en bloques utilizando código de borrado.""" 
    data = request.json.get('folder') 
    return reconstruction.encode_disk(data)

@reconstruction_blueprint.route('/api/decode_disk', methods=['POST'])
def decode_disk():
    """Reconstruye el contenido de un disco a partir de sus fragmentos de bloques.""" 
    data = request.json.get('folder') 
    return reconstruction.decode_disk(data)

@reconstruction_blueprint.route('/api/get_subdirectories', methods=['GET'])
def get_subdirectories():
    return reconstruction.get_subdirectories()
