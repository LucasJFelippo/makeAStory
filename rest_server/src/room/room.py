from flask import session, request
from flask_socketio import Namespace, emit, join_room, leave_room
from flask_jwt_extended import decode_token
from models import User
import json

from src.data import ROOMS, USER_ROOM_MAP, RoomState, MAX_ROOM_SIZE, MAX_SNIPPET_SIZE, GPT_SNIPPETS_TEMPLATE
from src.llm.gpt import submit_round

from src.log import logger


class RoomNS(Namespace):
    def __init__(self, namespace, socketio):
        super().__init__(namespace)
        self.socketio = socketio

    def _get_auth_info(self):
        user_id = session.get('user_id')
        username = session.get('username', 'Convidado')
        if not user_id:
            logger.warning("Tentativa de ação no RoomNS sem user_id na sessão")
        return user_id, username

    def on_connect(self, auth):
        token = auth.get('token') if auth else None

        # Adicionada autenticação do usuário
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
            emit('connect_ack')

        except Exception as e:
            logger.warning(f"Conexão com token inválido: {e}")
            raise ConnectionRefusedError('unauthorized - invalid token')
        emit('connect_confirm', {'sid': request.sid})


    def on_join_room(self, data):
        user_id, username = self._get_auth_info()
        if not user_id:
            return {'status': 'error', 'msg': 'usuário não autenticado'}

        room_data = data
        if isinstance(data, str):
            try:
                room_data = json.loads(data)
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar JSON do on_join_room: {data}")
                return {'status': 'error', 'msg': 'Dados de sala inválidos'}

        room_id_from_client = room_data.get('room_id')
        
        if room_id_from_client is None:
             logger.warning(f"on_join_room recebido sem 'room_id': {room_data}")
             return {'status': 'error', 'msg': 'room_id não fornecido'}

        try:
            room_id = int(room_id_from_client) 
        except (ValueError, TypeError):
            logger.warning(f"room_id inválido recebido: {room_id_from_client}")
            return {'status': 'error', 'msg': 'room_id deve ser um número'}

        if not room_id in ROOMS:
            logger.warning(f'[ROOM] User {username} (ID: {user_id}) pediu para entrar na sala {room_id} (inexistente)')
            return {'status': 'error', 'msg': "A sala não existe.", 'room_id': room_id}
        
        if len(ROOMS[room_id]['room_members']) >= MAX_ROOM_SIZE:
            logger.warning(f'[ROOM] User {username} (ID: {user_id}) tentou entrar na sala {room_id} (cheia)')
            return {'status': 'error', 'msg': 'A sala está cheia', 'room_id': room_id}

        logger.info(f'[ROOM {room_id}] User {username} (ID: {user_id}) entrou')

        # Adiciona o usuário (pelo ID do DB) à sala
        ROOMS[room_id]['room_members'][user_id] = {
            'user_id': user_id,
            'username': username, # Armazena o username
            'submitted': False,
            'snippet': ''
        }
        USER_ROOM_MAP[user_id] = room_id
        
        # Inscreve o cliente no canal da sala para broadcasts
        join_room(room_id)
        
        # Avisa os outros que o usuário entrou
        emit('status_update', {'msg': f'{username} entrou na sala.'}, to=room_id, include_self=False)

        return {'status': 'ok', 'room_id': room_id}

    """     def on_join_room(self, data): # MODIFICAR/ADICIONAR AUTENTICAÇÃO DO USER
            user_id = request.sid
            room_id = data.get('room_id')

            if not room_id in ROOMS:
                logger.warning(f'[ROOM] User {request.sid} asked to join a non existing room')
                return {'status': 'error', 'msg': "room didn't exist, what are you trying to do?", 'room_id': room_id}
            
            if len(ROOMS[room_id]['room_members']) >= MAX_ROOM_SIZE:
                return {'status': 'error', 'msg': 'room is full' , 'room_id': room_id}

            logger.info(f'[ROOM {room_id}] User {request.sid} asked to join')

            # room_members schema {
            #     'user_id': str,       > socket id
            #     'submitted': bool,    > if user have submitted the snippet in current round
            #     'snippet': str        > snippet of current round
            # }

            ROOMS[room_id]['room_members'][user_id] = {
                'user_id': user_id,
                'submitted': False,
                'snippet': ''
            }
            USER_ROOM_MAP[user_id] = room_id

            return {'status': 'ok', 'room_id': room_id} """
    
    def on_disconnect(self):
        user_id, username = self._get_auth_info()

        if not user_id or user_id not in USER_ROOM_MAP:
            logger.info(f"Disconnect de SID {request.sid} sem user_id mapeado.")
            return

        room_id = USER_ROOM_MAP[user_id]
        room = ROOMS.get(room_id)

        # Remove o cliente do canal de broadcast
        leave_room(room_id)

        if room:
            # Remove o usuário da lista de membros da sala
            if user_id in room['room_members']:
                room['room_members'].pop(user_id)
            
            # Avisa os outros que o usuário saiu
            emit('status_update', {'msg': f'{username} saiu.'}, to=room_id)
            logger.info(f"User {username} (ID: {user_id}) removido da sala {room_id}")

        # Remove o usuário do mapa global
        if user_id in USER_ROOM_MAP:
            USER_ROOM_MAP.pop(user_id)
        

    def on_start_game(self):
        user_id, username = self._get_auth_info()

        if not user_id or user_id not in USER_ROOM_MAP:
            logger.warning(f'[ROOM] User {username} tried to start a game but is not in a room')
            return {'status': 'error', 'msg': 'not in room'}

        room = ROOMS[USER_ROOM_MAP[user_id]]

        if room['room_state'] != RoomState.WAITING:
            logger.warning(f'[ROOM {USER_ROOM_MAP[user_id]}] User {username} tried to start a game but room state {room['room_state']}')
            # return {'status': 'error', 'msg': 'room not waiting'}

        logger.info(f'[ROOM {USER_ROOM_MAP[user_id]}] User {username} started the game')

        self.start_game(USER_ROOM_MAP[user_id], user_id)


    def on_story_snippet(self, data): # ADICIONAR USUARIO
        user_id, username = self._get_auth_info()

        if not user_id in USER_ROOM_MAP:
            logger.warning(f'[ROOM] User {username} (ID: {user_id}) tentou enviar snippet mas não está em sala')
            return {'status': 'error', 'msg': 'Você não está em uma sala'}

        snippet_data = data
        if isinstance(data, str):
            try:
                snippet_data = json.loads(data)
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar JSON do on_story_snippet: {data}")
                return {'status': 'error', 'msg': 'Dados de snippet inválidos'}

        snippet = snippet_data.get('snippet')
        if not snippet:
             return {'status': 'error', 'msg': 'Snippet não pode ser vazio'}

        room = ROOMS[USER_ROOM_MAP[user_id]]
        if room['room_state'] != RoomState.SNIPPETING:
            logger.warning(f'[ROOM {USER_ROOM_MAP[user_id]}] User {username} tentou enviar snippet mas o estado é {room['room_state']}')
            return {'status': 'error', 'msg': 'Não é hora de enviar snippets'}
        
        if len(snippet) > MAX_SNIPPET_SIZE:
            logger.warning(f'[ROOM {USER_ROOM_MAP[user_id]}] User {username} enviou snippet muito longo')
            return {'status': 'error', 'msg': f'Snippet muito longo (max: {MAX_SNIPPET_SIZE})'}

        members = room['room_members']
        if not members[user_id]['submitted']:
            members[user_id]['submitted'] = True
            room['pending'] -= 1

        members[user_id]['snippet'] = snippet
        
        logger.info(f"[ROOM {USER_ROOM_MAP[user_id]}] Snippet recebido de {username} (ID: {user_id})")

        emit('snippet_received', {'username': username}, to=USER_ROOM_MAP[user_id])

        if room['pending'] == 0:
            self.end_round(USER_ROOM_MAP[user_id], 'all_snippets_received')

        return {'status': 'ok'}
    

    
    def start_game(self, room_id, user_id):
        room = ROOMS[room_id]
        
        logger.info(f'[ROOM {room_id}] O jogo começou')
        
        # Pega o username de quem iniciou
        triggerer_username = room['room_members'].get(user_id, {}).get('username', 'Sistema')

        # Emite para todos na sala (canal)
        self.socketio.emit('game_started', {'triggerer': triggerer_username}, to=room_id)
        self.start_round(room_id, 'game_start')

    def start_round(self, room_id, trigger = None):
        room = ROOMS[room_id]
        room['room_state'] = RoomState.SNIPPETING
        room['pending'] = len(room['room_members'])
        room['current_round'] += 1
        
        logger.info(f'[ROOM {room_id}] Room started the round {room['current_round']} by trigger {trigger}')

        for member_id in room['room_members']:
            room['room_members'][member_id]['submitted'] = False
            room['room_members'][member_id]['snippet'] = ''

        self.socketio.emit('round_started', {
            'triggerer': trigger, 
            'round': room['current_round']
        }, to=room_id)
        # TODO: Implementar timer

    def end_round(self, room_id, trigger):
        room = ROOMS[room_id]
        room['room_state'] = RoomState.RESPONSE
        
        logger.info(f'[ROOM {room_id}] Room round {room['current_round']} ended by trigger {trigger}')
        
        members = room['room_members']
        snippets = []
        history_registry = {
            'round': room['current_round'],
            'snippets': {}
            }
        
        for member_id, member_data in members.items():
            snippet = member_data['snippet']
            username = member_data.get('username', member_id) # Usa username se tiver

            history_registry['snippets'][username] = snippet # Salva no histórico com username

            snippets.append({
                'sender_username': username,
                'snippet': snippet
            })

        room['history'].append(history_registry)
        
        self.socketio.emit('round_ended', {'snippets': snippets}, to=room_id)
        self.socketio.start_background_task(self.process_round, room_id, snippets)

    def process_round(self, room_id, snippets):
        room = ROOMS[room_id]
        current_round = room['current_round']

        snippets_str = ''
        for snippet_data in snippets:
            snippets_str += f"- {snippet_data['sender_username']}: {snippet_data['snippet']}\n"
        
        prompt = GPT_SNIPPETS_TEMPLATE.substitute(cround = current_round, snippets = snippets_str)
        
        room['history_parsed'].append({
            'role': 'user',
            'content': prompt
        })
        
        try:
            logger.info(f"[ROOM {room_id}] Enviando prompt para a IA...")
            response = submit_round(room['history_parsed']) 
            
            ia_text_response = response
            
            room['history_parsed'].append({
                'role': 'assistant',
                'content': ia_text_response
            })

            logger.info(f"[ROOM {room_id}] Resposta da IA recebida.")
            logger.info(ia_text_response)

            self.socketio.emit('new_story_part', {'text': ia_text_response}, to=room_id)
            self.start_round(room_id, 'ia_finished')

        except Exception as e:
            logger.error(f"[ROOM {room_id}] Erro ao processar a rodada com a IA: {e}")
            
            self.socketio.emit('error', {'msg': 'Erro na IA, a rodada será reiniciada.'}, to=room_id)
            self.start_round(room_id, 'ia_error')