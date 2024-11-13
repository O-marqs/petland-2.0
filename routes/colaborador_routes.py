from flask import Blueprint, request, jsonify
from models.colaborador import Colaborador

colaborador_bp = Blueprint('colaborador_bp', __name__)

@colaborador_bp.route('/colaborador', methods=['POST'])
def cadastrar_colaborador():
    data = request.json
    response = Colaborador.cadastrar_colaborador(data)
    return jsonify(response)

@colaborador_bp.route('/colaborador/login', methods=['POST'])
def login_colaborador():
    data = request.json
    email = data['email']
    senha = data['senha']
    response = Colaborador.login_colaborador(email, senha)
    return jsonify(response)

@colaborador_bp.route('/colaborador/<cpf_colaborador>', methods=['GET'])
def buscar_colaborador(cpf_colaborador):
    colaborador = Colaborador.buscar_colaborador(cpf_colaborador)
    return jsonify(colaborador)

@colaborador_bp.route('/colaborador/<cpf_colaborador>', methods=['PUT'])
def atualizar_colaborador(cpf_colaborador):
    data = request.json
    response = Colaborador.atualizar_colaborador(cpf_colaborador, data)
    return jsonify(response)

@colaborador_bp.route('/colaborador/<cpf_colaborador>', methods=['DELETE'])
def deletar_colaborador(cpf_colaborador):
    response = Colaborador.deletar_colaborador(cpf_colaborador)
    return jsonify(response)
