from flask_socketio import Namespace, emit
from models import GameRoom, db


class LobbyNS(Namespace):
    # --- CORREÇÃO: Aceite 'app' no construtor ---
    def __init__(self, namespace, app):
        super().__init__(namespace)
        self.app = app

    def _get_and_emit_rooms(self):
        """
        Busca salas no DB e emite 'rooms_info' para todos no namespace.
        Precisa ser chamado de dentro de um app_context.
        """
        rooms_info = []
        try:
            # --- CORREÇÃO: Use o app_context ---
            with self.app.app_context():
                # Use .count() para ser mais eficiente do que .all()
                db_rooms = GameRoom.query.filter_by(status='LOBBY').all()
                rooms_info = [{
                    'room_id': room.id,
                    'room_name': room.room_code,
                    'members': room.participants.count() # Isso agora será correto
                } for room in db_rooms]
        except Exception as e:
            print(f"Erro ao buscar salas do lobby: {e}")
            
        # Emite para TODOS os clientes conectados a este namespace ('/')
        emit('rooms_info', {'rooms': rooms_info})

    def on_connect(self):
        # Envia a lista de salas assim que o cliente se conecta
        self._get_and_emit_rooms()