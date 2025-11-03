from flask import Flask
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from datetime import timedelta

from src.lobby.lobby import LobbyNS
from src.room.room import RoomNS
from src.auth import auth_bp
from REST.routes import api as api_blueprint
from models import db, bcrypt, socketio

import os

def create_app():
    app = Flask(__name__)

    is_production = os.environ.get('NODE_ENV') == 'production'
    app.debug = not is_production 

    app.config['SECRET_KEY'] = os.getenv('MAKEASTORY_SOCKETIO_APP_KEY')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'chave-jwt')

    default_db = 'sqlite:///game_data.db'
    db_url = os.environ.get('DATABASE_URL', default_db)
    
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
    
    app.config['SQLALCHEMY_POOL_PRE_PING'] = True 
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 300
    
    db.init_app(app)
    bcrypt.init_app(app)
    jwt = JWTManager(app)

    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173') 
    
    CORS(app, 
         origins=[frontend_url], 
         methods=["GET", "POST", "OPTIONS"], 
         headers=["Content-Type", "Authorization"], 
         supports_credentials=True
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_blueprint)
    
    lobby_handler = LobbyNS(app)
    room_handler = RoomNS(socketio, app)
    socketio.on_namespace(lobby_handler)
    socketio.on_namespace(room_handler)

    socketio.init_app(app, 
                        cors_allowed_origins=frontend_url)
    
    return app, socketio