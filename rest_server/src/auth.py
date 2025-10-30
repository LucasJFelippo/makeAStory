from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, bcrypt, User

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"msg": "Campos 'username', 'email' e 'password' são obrigatórios"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username já existe"}), 409
    
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email já está em uso"}), 409

    new_user = User(username=username, email=email)
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "msg": "Usuário criado com sucesso",
        "user": {
            "id": new_user.public_id,
            "username": new_user.username,
            "email": new_user.email
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "Campos 'username' e 'password' são obrigatórios"}), 400

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        user.last_login = datetime.utcnow()
        db.session.commit()
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token)

    return jsonify({"msg": "Usuário ou senha inválidos"}), 401

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"msg": "Usuário não encontrado"}), 404

    return jsonify({
        "id": user.public_id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at
    })