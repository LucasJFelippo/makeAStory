from flask import session, request
import requests
import os
from flask_socketio import Namespace, emit, join_room, leave_room
from flask_jwt_extended import decode_token
from models import User, db, GameRoom
import json

from src.data import (
    ROOMS, USER_ROOM_MAP, RoomState, MAX_ROOM_SIZE, 
    MAX_SNIPPET_SIZE, GPT_SNIPPETS_TEMPLATE, GPT_ENTRY_PROMPT
)

from src.data import ROOMS, USER_ROOM_MAP, RoomState, MAX_ROOM_SIZE, MAX_SNIPPET_SIZE, GPT_SNIPPETS_TEMPLATE
from src.llm.gpt import submit_round

from src.log import logger


class RoomNS(Namespace):
    def __init__(self, namespace, socketio, app):
        super().__init__(namespace)
        self.socketio = socketio
        self.app = app

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

        game_room_db = GameRoom.query.get(room_id)

        if not game_room_db:
            logger.warning(f'[ROOM] User {username} (ID: {user_id}) pediu para entrar na sala {room_id} (inexistente no DB)')
            return {'status': 'error', 'msg': "A sala não existe.", 'room_id': room_id}
        
        if room_id not in ROOMS:
            logger.info(f"[ROOM {room_id}] Sala '{game_room_db.room_code}' está inativa. Ativando e hidratando cache...")
            ROOMS[room_id] = {
                'room_id': game_room_db.id,
                'room_name': game_room_db.room_code,
                'room_state': RoomState.WAITING,
                'room_members': {},
                'pending': 0,
                'timer': None,
                'history': [],
                'history_parsed': [{
                    'role': 'developer',
                    'content': GPT_ENTRY_PROMPT
                }],
                'current_round': 0
            }
        
        if len(ROOMS[room_id]['room_members']) >= MAX_ROOM_SIZE:
            logger.warning(f'[ROOM] User {username} (ID: {user_id}) tentou entrar na sala {room_id} (cheia no cache)')
            return {'status': 'error', 'msg': 'A sala está cheia', 'room_id': room_id}
        
        # O usuário já está na sala?
        if user_id in ROOMS[room_id]['room_members']:
             logger.info(f"[ROOM {room_id}] User {username} (ID: {user_id}) já está na sala.")
        else:
            logger.info(f'[ROOM {room_id}] User {username} (ID: {user_id}) entrou')

        # Adiciona o usuário (pelo ID do DB) à sala (em memória)
        ROOMS[room_id]['room_members'][user_id] = {
            'user_id': user_id,
            'username': username, # Armazena o username
            'submitted': False,
            'snippet': ''
        }
        USER_ROOM_MAP[user_id] = room_id
        
        # Cliente entra no canal da sala para broadcasts
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

            if len(room['room_members']) == 0:
                logger.info(f"[ROOM {room_id}] A sala está vazia. Removendo do cache de memória.")
                ROOMS.pop(room_id, None)
                
                try:
                    game_room_db = GameRoom.query.get(room_id)
                    if game_room_db:
                        game_room_db.status = 'LOBBY'
                        # game_room_db.final_story_text = ""
                        db.session.commit()
                except Exception as e:
                    logger.error(f"Erro ao resetar status da sala {room_id} no DB: {e}")
                    db.session.rollback()

        # Remove o usuário do mapa global
        if user_id in USER_ROOM_MAP:
            USER_ROOM_MAP.pop(user_id)
        
        try:
            user = User.query.get(user_id)
            if user and user.is_guest:
                logger.info(f"Convidado {username} (ID: {user_id}) desconectou. Removendo do banco de dados.")
                db.session.delete(user)
                db.session.commit()
                logger.info(f"Convidado {username} (ID: {user_id}) removido com sucesso.")

        except Exception as e:
            logger.error(f"Erro ao tentar remover convidado {user_id}: {e}")
            db.session.rollback()
        

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

        try:
            game_room_db = GameRoom.query.get(USER_ROOM_MAP[user_id])
            if game_room_db:
                game_room_db.status = 'IN_PROGRESS'
                db.session.commit()
        except Exception as e:
            logger.error(f"Erro ao atualizar status da sala {USER_ROOM_MAP[user_id]} no DB: {e}")
            db.session.rollback()

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
        self.socketio.emit('game_started', {'triggerer': triggerer_username}, to=room_id, namespace='/r')
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
        }, to=room_id, namespace='/r')
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
        
        self.socketio.emit('round_ended', {'snippets': snippets}, to=room_id, namespace='/r')
        self.socketio.start_background_task(self.process_round, room_id, snippets, self.app)

    def process_round(self, room_id, snippets, app):
        with app.app_context():
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

                theme = None
                music_url = None

                try:
                    theme_prompt = [
                        {
                            'role': 'system', 
                            'content': (
                                "Sua tarefa é extrair o 'clima' ou 'sentimento' de um texto. "
                                "Forneça de 5 a 7 tags em inglês que descrevam o GÊNERO (ex: medieval fantasy, sci-fi) "
                                ",os instrumentos a serem utilizados na musica e a EMOÇÃO (ex: epic, battle, sad, mysterious, rainy), não os objetos. "
                                "EVITE tags de objetos literais como 'dragon', 'bard' ou 'sword'. "
                                "Responda apenas com as tags separadas por vírgula."
                            )
                        },
                        {'role': 'user', 'content': ia_text_response}
                    ]
                    tags_str = submit_round(theme_prompt).strip().lower()
                    theme = tags_str.replace(',', ' ').replace('  ', ' ')
                    logger.info(f"[ROOM {room_id}] Temas extraídos: {theme}")
                    
                except Exception as e:
                    logger.warning(f"[ROOM {room_id}] Não foi possível extrair os temas: {e}")

                try:
                    game_room_db = GameRoom.query.get(room_id)
                    if game_room_db:
                        if game_room_db.final_story_text is None:
                            game_room_db.final_story_text = ""
                        game_room_db.final_story_text += f"\n\n--- Round {current_round} ---\n{ia_text_response}"
                        db.session.commit()

                except Exception as e:
                    logger.error(f"Erro ao salvar história no DB da sala {room_id}: {e}")
                    db.session.rollback()
                    

                if theme:
                    try:
                        JAMENDO_CLIENT_ID = os.getenv('JAMENDO_CLIENT_ID')
                        if JAMENDO_CLIENT_ID:
                            jamendo_url = "https://api.jamendo.com/v3.0/tracks/"
                            params = {
                                'client_id': JAMENDO_CLIENT_ID,
                                'format': 'json',
                                'limit': 1,
                                'search': theme,
                                'order': 'relevance',
                                'vocalinstrumental': 'instrumental'
                            }
                            r = requests.get(jamendo_url, params=params, timeout=5)
                            r.raise_for_status()
                            jamendo_data = r.json()
                            
                            if jamendo_data.get('results') and len(jamendo_data['results']) > 0:
                                music_url = jamendo_data['results'][0].get('audio')
                                logger.info(f"[ROOM {room_id}] URL de música do Jamendo encontrada: {music_url}")
                            else:
                                logger.warning(f"[ROOM {room_id}] Nenhuma música encontrada no Jamendo para o tema: {theme}")
                        else:
                            logger.warning(f"[ROOM {room_id}] JAMENDO_CLIENT_ID não configurada. Pulando música.")
                    except Exception as e:
                        logger.error(f"[ROOM {room_id}] Erro ao chamar API do Jamendo: {e}")


                self.socketio.emit('new_story_part', {
                    'text': ia_text_response,
                    'music_url': music_url
                }, to=room_id, namespace='/r')
                
                self.start_round(room_id, 'ia_finished')

            except Exception as e:
                logger.error(f"[ROOM {room_id}] Erro ao processar a rodada com a IA: {e}")
                
                self.socketio.emit('error', {'msg': 'Erro na IA, a rodada será reiniciada.'}, to=room_id, namespace='/r')
                self.start_round(room_id, 'ia_error')