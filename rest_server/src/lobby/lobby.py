from flask_socketio import Namespace, emit
from models import GameRoom, db


class LobbyNS(Namespace):
    def __init__(self, namespace, app):
        super().__init__(namespace)
        self.app = app

    def _get_and_emit_rooms(self):
        rooms_info = []
        try:
            with self.app.app_context():
                db_rooms = GameRoom.query.filter(
                    GameRoom.status.in_(['LOBBY', 'IN_PROGRESS'])
                ).all()
                rooms_info = [{
                    'room_id': room.id,
                    'room_name': room.room_code,
                    'members': room.participants.count(),
                    'status': room.status
                } for room in db_rooms]
        except Exception as e:
            print(f"Erro ao buscar salas do lobby: {e}")
            
        emit('rooms_info', {'rooms': rooms_info})

    def on_connect(self):
        self._get_and_emit_rooms()