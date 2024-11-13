from flask import Blueprint, request, jsonify
from models.servico import Servico

servico_bp = Blueprint('servico_bp', __name__)

@servico_bp.route('/servico', methods=['POST'])
def cadastrar_servico():
    data = request.json
    response = Servico.cadastrar_servico(data)
    return jsonify(response)

@servico_bp.route('/servico/<id_servico>', methods=['GET'])
def buscar_servico(id_servico):
    servico = Servico.buscar_servico(id_servico)
    return jsonify(servico)

@servico_bp.route('/servico/<id_servico>', methods=['PUT'])
def atualizar_servico(id_servico):
    data = request.json
    response = Servico.atualizar_servico(id_servico, data)
    return jsonify(response)

@servico_bp.route('/servico/<id_servico>', methods=['DELETE'])
def deletar_servico(id_servico):
    response = Servico.deletar_servico(id_servico)
    return jsonify(response)
