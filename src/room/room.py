from flask import session, request
from flask_socketio import Namespace, emit, join_room, leave_room
from flask_jwt_extended import decode_token
from models import User
import json

from src.data import ROOMS, USER_ROOM_MAP, RoomState

from src.log import logger

class RoomNS(Namespace):

    def _get_auth_info(self):
        user_id = session.get('user_id')
        username = session.get('username', 'Convidado')
        if not user_id:
            logger.warning("Tentativa de ação no RoomNS sem user_id na sessão")
        return user_id, username

    def on_connect(self, auth):
        token = auth.get('token') if auth else None
        print("--- MÉTODO ON_CONNECT DO ROOMNS FOI ACIONADO! ---")

        if not token:
            print("--- CONEXÃO REJEITADA: SEM TOKEN ---")
            logger.warning(f"Conexão rejeitada no RoomNS (sem token) do sid: {request.sid}")
            raise ConnectionRefusedError('unauthorized - no token')

        try:
            token_data = decode_token(token)
            user_id = token_data['sub']
            user = User.query.get(user_id)

            if not user:
                 raise ConnectionRefusedError('unauthorized - user not found')

            # SALVA O ID E USERNAME NA SESSÃO DO SOCKET
            session['user_id'] = user.id
            session['username'] = user.username
            logger.info(f'[ROOM] Conexão autenticada para {user.username} (ID: {user.id}) (sid: {request.sid})')
        
        except Exception as e:
            logger.warning(f"Conexão com token inválido: {e}")
            raise ConnectionRefusedError('unauthorized - invalid token')
        emit('connect_confirm', {'sid': request.sid})
        
    def on_join_room(self, data):
        user_id, username = self._get_auth_info()
        if not user_id:
            return  # Ignora se não estiver autenticado

        room_data = data
        if isinstance(data, str):
            try:
                room_data = json.loads(data)
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar JSON do on_join_room: {data}")
                emit('error', {'msg': 'Dados de sala inválidos'}, to=request.sid)
                return
            
        room_id_from_client = room_data.get('room_id')
        
        if room_id_from_client is None:
             logger.warning(f"on_join_room recebido sem 'room_id': {room_data}")
             emit('error', {'msg': 'room_id não fornecido'}, to=request.sid)
             return
        
        try:
            room_id = int(room_id_from_client) 
        except (ValueError, TypeError):
            logger.warning(f"room_id inválido recebido: {room_id_from_client}")
            emit('error', {'msg': 'room_id deve ser um número'}, to=request.sid)
            return

        logger.info(f'[ROOM] User {username} (ID: {user_id}) pediu para entrar na sala {room_id}')


        if room_id in ROOMS:
            # Adiciona o usuário (pelo ID do DB) ao estado do jogo em memória
            ROOMS[room_id]['room_members'][user_id] = {
                'user_id': user_id,
                'username': username,
                'submitted': False,
                'snippet': ''
            }

            USER_ROOM_MAP[user_id] = room_id
            join_room(room_id)

            emit('joined_room', {'room_id': room_id}, to=request.sid)
            emit('status_update', {'msg': f'{username} entrou na sala.'}, to=room_id, include_self=False)
        else:
            logger.warning(f"User {username} tentou entrar em sala {room_id} inexistente.")
            emit('error', {'msg': 'Sala não encontrada'}, to=request.sid)
    
    def on_disconnect(self):
        user_id, username = self._get_auth_info()

        if not user_id or user_id not in USER_ROOM_MAP:
            logger.info(f"Disconnect de SID {request.sid} sem user_id mapeado.")
            return

        room_id = USER_ROOM_MAP[user_id]
        room = ROOMS.get(room_id)

        leave_room(room_id)

        if room:
            if user_id in room['room_members']:
                room['room_members'].pop(user_id)
            
            emit('status_update', {'msg': f'{username} saiu.'}, to=room_id)
            logger.info(f"User {username} (ID: {user_id}) removido da sala {room_id}")

        if user_id in USER_ROOM_MAP:
            USER_ROOM_MAP.pop(user_id)
        

    def on_start_game(self):
        user_id, username = self._get_auth_info()
        if not user_id or user_id not in USER_ROOM_MAP:
            return

        room_id = USER_ROOM_MAP[user_id]
        logger.info(f"User {username} (ID: {user_id}) iniciou o jogo na sala {room_id}")
        
        self.start_game(room_id, user_id)


    def on_story_snippet(self, data):
        user_id, username = self._get_auth_info()
        if not user_id or user_id not in USER_ROOM_MAP:
            return

        snippet_data = data
        if isinstance(data, str):
            try:
                snippet_data = json.loads(data)
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar JSON do on_story_snippet: {data}")
                emit('error', {'msg': 'Dados de snippet inválidos'}, to=request.sid)
                return

        snippet = snippet_data.get('snippet')
        
        if not snippet:
            logger.warning(f"on_story_snippet recebido sem 'snippet': {snippet_data}")
            return 

        room_id = USER_ROOM_MAP[user_id]
        room = ROOMS.get(room_id)
        if not room:
            return

        members = room['room_members']
        if user_id not in members:
            return

        if not members[user_id]['submitted']:
            room['pending'] -= 1

        members[user_id]['submitted'] = True
        members[user_id]['snippet'] = snippet

        emit('snippet_broadcast', {
            'sender_username': username,
            'snippet': snippet
        }, to=room_id)
        
        logger.info(f"Snippet recebido de {username} para sala {room_id}")

        if room['pending'] == 0:
            self.end_round(room_id)

    def start_game(self, room_id, triggerer_id=None):
        logger.info(f"GAME START para sala {room_id}")
        triggerer_username = "Sistema"
        if triggerer_id and triggerer_id in ROOMS[room_id]['room_members']:
             triggerer_username = ROOMS[room_id]['room_members'][triggerer_id]['username']
             
        self.start_round(room_id, triggerer_username)

    def start_round(self, room_id, triggerer_username="Sistema"):
        room = ROOMS[room_id]
        room['room_state'] = RoomState.SNIPPETING
        room['pending'] = len(room['room_members'])
        
        for member in room['room_members'].values():
            member['submitted'] = False
            member['snippet'] = ''

        emit('game_started', {'triggerer': triggerer_username}, to=room_id)
        logger.info(f"Rodada iniciada para sala {room_id}")
        # TODO: Implement timming

    def end_round(self, room_id):
        room = ROOMS[room_id]
        room['room_state'] = RoomState.READING # Muda o estado

        # Coleta todos os snippets e usernames
        snippets_data = []
        for member in room['room_members'].values():
            snippets_data.append({
                'username': member.get('username', '???'),
                'snippet': member['snippet']
            })
        
        logger.info(f"Rodada finalizada para sala {room_id}. Snippets: {snippets_data}")

        # Notifica os clientes que a rodada terminou e envia os dados
        emit('round_ended', {
            'snippets': snippets_data,
            'round_number': room['current_round']
        }, to=room_id)
        
        room['current_round'] += 1
        # TODO: Chamar a IA, depois chamar self.start_round()