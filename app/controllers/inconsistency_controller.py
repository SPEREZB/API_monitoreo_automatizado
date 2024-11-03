from flask import Blueprint, request, jsonify
from zfec import filefec
import os
from app.models.alert_model import AlertModel
from app.services.inconsistency_service import InconsistencyService

inconsistencia_blueprint = Blueprint('inconsistencia', __name__)
inconsistencia_service = InconsistencyService()  
 
@inconsistencia_blueprint.route('/api/inconsistencias', methods=['GET'])
def get_inconsistencias():
    try:
        inconsistencias = inconsistencia_service.get_inconsistencias()  
        return jsonify(inconsistencias), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
@inconsistencia_blueprint.route('/api/analizar', methods=['POST'])
def analyze_inconsistencies():
    try: 
        data = request.json.get('folder') 
        inconsistencia_service.__init__(data)
        resultado = inconsistencia_service.analyze_inconsistencies()  
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
@inconsistencia_blueprint.route('/api/resolver', methods=['POST'])
def resolve_inconsistencies():
    data = request.json
    try:
        data = request.json.get('folder') 
        inconsistencia_service.__init__(data) 
        inconsistencia_service.resolve_inconsistencies()  
        return jsonify({"message": "Inconsistency resolved"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500  