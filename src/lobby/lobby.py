from flask_socketio import Namespace, emit

from src.data import ROOMS


class LobbyNS(Namespace):
    def on_connect(self):
        print("--- ALERTA: CLIENTE CONECTOU NO LOBBYNS (/) ---")
        rooms_info = [{
            'room_id': info['room_id'],
            'room_name': info['room_name'],
            'members': len(info['room_members'])
        } for info in ROOMS.values()]

        emit('rooms_info', {'rooms': rooms_info})