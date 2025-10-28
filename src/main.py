from flask import Flask, session, request
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager, decode_token

from src.lobby.lobby import LobbyNS
from src.room.room import RoomNS
from src.auth import auth_bp
from REST.routes import api as api_blueprint
from models import db, bcrypt, User

import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('MAKEASTORY_SOCKETIO_APP_KEY', 'chave-sessao')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'chave-jwt')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game_data.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    bcrypt.init_app(app)
    jwt = JWTManager(app)
    socketio = SocketIO(cors_allowed_origins='*')

    app.register_blueprint(auth_bp)       # Registra /auth/register, /auth/login, etc.
    app.register_blueprint(api_blueprint) # Registra /api/rooms, /api/rooms/<id>/join, etc.

    socketio.on_namespace(LobbyNS('/'))
    socketio.on_namespace(RoomNS('/r'))

    socketio.init_app(app)

    return app, socketio