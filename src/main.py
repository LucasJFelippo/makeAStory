from flask import Flask
from flask_socketio import SocketIO

from src.lobby.lobby import LobbyNS
from src.room.room import RoomNS

import os


def create_app():
    app = Flask(__name__)
    app.debug = True
    app.config['SECRET_KEY'] = os.getenv('MAKEASTORY_SOCKETIO_APP_KEY')

    socketio = SocketIO(cors_allowed_origins='*')
    
    socketio.on_namespace(LobbyNS('/'))
    socketio.on_namespace(RoomNS('/r', socketio))

    socketio.init_app(app)

    return app, socketio