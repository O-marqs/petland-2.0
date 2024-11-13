from flask import Blueprint, request, jsonify
from models.pet import Pet

pet_bp = Blueprint('pet_bp', __name__)

@pet_bp.route('/pet', methods=['POST'])
def cadastrar_pet():
    data = request.json
    response = Pet.cadastrar_pet(data)
    return jsonify(response)

@pet_bp.route('/pet/<id_pet>', methods=['GET'])
def buscar_pet(id_pet):
    pet = Pet.buscar_pet(id_pet)
    return jsonify(pet)

@pet_bp.route('/pet/<id_pet>', methods=['PUT'])
def atualizar_pet(id_pet):
    data = request.json
    response = Pet.atualizar_pet(id_pet, data)
    return jsonify(response)

@pet_bp.route('/pet/<id_pet>', methods=['DELETE'])
def deletar_pet(id_pet):
    response = Pet.deletar_pet(id_pet)
    return jsonify(response)
