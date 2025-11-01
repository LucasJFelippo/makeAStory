from flask_socketio import Namespace, emit
from models import GameRoom, db


class LobbyNS(Namespace):
    def on_connect(self):

        try:
            db_rooms = GameRoom.query.filter_by(status='LOBBY').all()

            rooms_info = [{
                'room_id': room.id,
                'room_name': room.room_code,
                'members': len(room.participants.all())
            } for room in db_rooms]

            emit('rooms_info', {'rooms': rooms_info})
            
        except Exception as e:
            print(f"Erro ao buscar salas do lobby: {e}")
            emit('rooms_info', {'rooms': []})

        emit('rooms_info', {'rooms': rooms_info})