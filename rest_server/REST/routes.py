import string
import random
from flask import Blueprint, jsonify
from flask_jwt_extended import (
    jwt_required, 
    get_jwt_identity
)

from models import db, User, GameRoom

api = Blueprint('api', __name__, url_prefix='/api')

def generate_room_code(length=6):
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not GameRoom.query.filter_by(room_code=code).first():
            return code

@api.route('/rooms', methods=['POST'])
@jwt_required()
def create_room():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    new_room = GameRoom(
        room_code=generate_room_code(),
        status='LOBBY'
    )
    new_room.participants.append(user)
    
    db.session.add(new_room)
    db.session.commit()

    return jsonify({
        "msg": "Sala criada com sucesso",
        "room": {
            "room_code": new_room.room_code,
            "status": new_room.status,
            "created_at": new_room.created_at
        }
    }), 201

@api.route('/rooms', methods=['GET'])
def list_rooms():
    rooms = GameRoom.query.filter_by(status='LOBBY').all()
    
    room_list = [
        {
            "room_code": room.room_code,
            "participants_count": room.participants.count(),
            "created_at": room.created_at
        } for room in rooms
    ]
    
    return jsonify(rooms=room_list)

@api.route('/rooms/<string:room_code>', methods=['GET'])
def get_room_details(room_code):
    room = GameRoom.query.filter_by(room_code=room_code.upper()).first()

    if not room:
        return jsonify({"msg": "Sala não encontrada"}), 404

    participants_list = [
        user.username for user in room.participants
    ]

    return jsonify({
        "room_code": room.room_code,
        "status": room.status,
        "participants": participants_list,
        "created_at": room.created_at
    })

@api.route('/rooms/<string:room_code>/join', methods=['POST'])
@jwt_required()
def join_game_room(room_code):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    room = GameRoom.query.filter_by(room_code=room_code.upper()).first()

    if not room:
        return jsonify({"msg": "Sala não encontrada"}), 404
        
    if room.status != 'LOBBY':
        return jsonify({"msg": "Não é possível entrar em uma sala que já começou"}), 403

    if user in room.participants:
        return jsonify({"msg": "Você já está nesta sala"}), 409

    room.participants.append(user)
    db.session.commit()

    return jsonify({
        "msg": f"Usuário {user.username} entrou na sala {room.room_code}"
    })