from flask import request
from flask_socketio import Namespace, emit

from src.data import ROOMS, USER_ROOM_MAP, RoomState, MAX_ROOM_SIZE, MAX_SNIPPET_SIZE, GPT_SNIPPETS_TEMPLATE
from src.llm.gpt import submit_round

from src.log import logger


class RoomNS(Namespace):
    def __init__(self, namespace, socketio):
        super().__init__(namespace)
        self.socketio = socketio

    def on_connect(self):
        logger.info(f'[ROOM] New connection from {request.sid}')
        emit('connect_ack')

    def on_join_room(self, data):
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

        return {'status': 'ok', 'room_id': room_id}
    
    def on_disconnect(self):
        user_id = request.sid
        # reason = self.server.disconnect_reason(user_id)
        
        # logger.info(f'[ROOM] User {request.sid} disconnected ({reason})')

        room = ROOMS[USER_ROOM_MAP[user_id]]
        room['room_members'].pop(user_id)
        USER_ROOM_MAP.pop(user_id)
        

    def on_start_game(self):
        user_id = request.sid

        if not user_id in USER_ROOM_MAP:
            logger.warning(f'[ROOM] User {request.sid} tried to start a game but is not in a room')
            return {'status': 'error', 'msg': 'not in room'}

        room = ROOMS[USER_ROOM_MAP[user_id]]

        if room['room_state'] != RoomState.WAITING:
            logger.warning(f'[ROOM {USER_ROOM_MAP[user_id]}] User {request.sid} tried to start a game but room state {room['room_state']}')
            # return {'status': 'error', 'msg': 'room not waiting'}

        logger.info(f'[ROOM {USER_ROOM_MAP[user_id]}] User {request.sid} started the game')

        self.start_game(USER_ROOM_MAP[user_id], user_id)


    def on_story_snippet(self, data):
        user_id = request.sid
        snippet = data.get('snippet')

        if not user_id in USER_ROOM_MAP:
            logger.warning(f'[ROOM] User {request.sid} tried to send a snippet but is not in a room')
            return {'status': 'error', 'msg': 'not in room'}


        room = ROOMS[USER_ROOM_MAP[user_id]]
        if room['room_state'] != RoomState.SNIPPETING:
            logger.warning(f'[ROOM {USER_ROOM_MAP[user_id]}] User {request.sid} tried to send a snippet but room state {room['room_state']}')
            return {'status': 'error', 'msg': 'room not reading'}
        
        if len(snippet) > MAX_SNIPPET_SIZE:
            return {'status': 'error', 'msg': 'size limit'}

        members = room['room_members']
        if not members[user_id]['submitted']:
            members[user_id]['submitted'] = True
            room['pending'] -= 1

        members[user_id]['snippet'] = snippet

        if room['pending'] == 0:
            self.end_round(USER_ROOM_MAP[user_id], 'all_snippets')

        return {'status': 'ok'}
            


    
    def start_game(self, room_id, user_id):
        room = ROOMS[room_id]
        
        logger.info(f'[ROOM {room_id}] Room started the game')

        for member in room['room_members']:
            emit('game_started', {'triggerer': user_id}, to=member)

        self.start_round(room_id, 'game_start')

    def start_round(self, room_id, trigger = None):
        room = ROOMS[room_id]
        room['room_state'] = RoomState.SNIPPETING
        room['pending'] = len(room['room_members'])
        room['current_round'] += 1
        
        logger.info(f'[ROOM {room_id}] Room started the round {room['current_round']} by trigger {trigger}')

        for member in room['room_members']:
            emit('round_started', {'triggerer': trigger}, to=member)
        # TODO: Implement timming

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
        for member_id, member in members.items():
            snippet = member['snippet']

            history_registry['snippets'][member_id] = snippet

            snippets.append({
                'sender': member_id,
                'snippet': member['snippet']
            })

        room['history'].append(history_registry)
        
        print(room['history'])
        
        members = room['room_members']
        for member_id, member in members.items():
            emit('snippet_broadcast', {'snippets': snippets}, to=member_id)

        self.socketio.start_background_task(self.process_round, room_id, snippets)

    def process_round(self, room_id, snippets):
        room = ROOMS[room_id]
        current_round = room['current_round']

        snippets_str = ''
        count = 1
        for snippet in snippets:
            snippets_str += f'{count}. {snippet['snippet']}\n'
            count += 1
        
        prompt = GPT_SNIPPETS_TEMPLATE.substitute(cround = current_round,snippets = snippets_str)
        
        room['history_parsed'].append({
            'role': 'user',
            'content': prompt
        })
        
        response = submit_round(room['history_parsed'])
        
        room['history_parsed'].append({
            'role': 'assistant',
            'content': response
        })
        
        members = room['room_members']
        for member_id, member in members.items():
            emit('ai_response', {'snippets': snippets}, to=member_id)