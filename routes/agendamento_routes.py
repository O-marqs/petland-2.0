from flask import Blueprint, request, jsonify
from models.agendamento import Agendamento

agendamento_bp = Blueprint('agendamento_bp', __name__)

@agendamento_bp.route('/agendamento', methods=['POST'])
def criar_agendamento():
    data = request.json
    response = Agendamento.criar_agendamento(data)
    return jsonify(response)

@agendamento_bp.route('/agendamento/<id_agendamento>', methods=['GET'])
def buscar_agendamento(id_agendamento):
    agendamento = Agendamento.buscar_agendamento(id_agendamento)
    return jsonify(agendamento)

@agendamento_bp.route('/agendamento/<id_agendamento>', methods=['PUT'])
def atualizar_agendamento(id_agendamento):
    data = request.json
    response = Agendamento.atualizar_agendamento(id_agendamento, data)
    return jsonify(response)

@agendamento_bp.route('/agendamento/<id_agendamento>', methods=['DELETE'])
def deletar_agendamento(id_agendamento):
    response = Agendamento.deletar_agendamento(id_agendamento)
    return jsonify(response)
