from flask import request
from flask_socketio import Namespace, emit

from src.data import ROOMS, USER_ROOM_MAP, RoomState

from src.log import logger

class RoomNS(Namespace):
    def on_connect(self):
        logger.info(f'[ROOM] New connection from {request.sid}')
        emit('connect_confirm', {'sid': request.sid})

    def on_join_room(self, data):
        user_id = request.sid
        room_id = data.get('room_id')

        logger.info(f'[ROOM] User {request.sid} asked to join {room_id}')

        if room_id in ROOMS:
            ROOMS[room_id]['room_members'][user_id] = {
                'user_id': user_id,
                'submitted': False,
                'snippet': ''
            }
            USER_ROOM_MAP[user_id] = room_id

            emit('joined_room', {'room_id': room_id}, to=user_id)
    
    def on_disconnect(self):
        user_id = request.sid

        room = ROOMS[USER_ROOM_MAP[user_id]]
        room['room_members'].pop(user_id)
        USER_ROOM_MAP.pop(user_id)
        

    def on_start_game(self):
        user_id = request.sid
        
        if not user_id in USER_ROOM_MAP:
            return

        self.start_game(USER_ROOM_MAP[user_id])


    def on_story_snippet(self, data):
        user_id = request.sid
        snippet = data.get('snippet')

        room = ROOMS[USER_ROOM_MAP[user_id]]
        members = room['room_members']
        
        if not members[user_id]['submitted']:
            room['pending'] -= 1


        members[user_id]['submitted'] = True
        members[user_id]['snippet'] = snippet

        for member_id in members:
            emit('snippet_broadcast', {'sender': user_id[:5], 'snippet': snippet}, to=member_id)

        if room['pending'] == 0:
            self.end_round(USER_ROOM_MAP[user_id])
            

    
    def start_game(self, room_id):
        print("GAME START")
        self.start_round(room_id)

    def start_round(self, room_id, user_id = None):
        room = ROOMS[room_id]
        room['room_state'] = RoomState.SNIPPETING
        room['pending'] = len(room['room_members'])
        
        if not user_id:
            user_id = 'Timed Out'
        
        for member in room['room_members']:
            emit('game_started', {'triggerer': user_id}, to=member)
        # TODO: Implement timming

    def end_round(self, room_id):
        room = ROOMS[room_id]
        room['room_state'] = RoomState.READING

        snippets = []
        for member_id, member in room['room_members'].items():
            snippets.append(member['snippet'])
        
        print(snippets)