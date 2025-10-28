from enum import Enum

class RoomState(Enum):
    WAITING = 0
    SNIPPETING = 1
    READING = 2

ROOMS_SAMPLE_STRUCTURE = {
    0: {
        'room_id': 0,
        'room_name': 'Room Name',

        'room_state': RoomState.WAITING,

        'room_members': {
                'someplayer1': {
                    'user_id': str,
                    'submitted': bool,
                    'snippet': str
                    
                }
            },

        'pending': 99,
        'timer': None,

        'history': [
            {
                'round': 1,
                'snippets': {
                    'someplayer1': "Once upon a time there was a dragon",
                    'someplayer2': "Once upon a time there was a princes",
                    'someplayer3': "Once upon a time there was a thief"
                    }
            }
        ],
        'current_round': 1
    }
}

ROOMS = {
    0: {
        'room_id': 0,
        'room_name': 'Sala do Luquinha',

        'room_state': RoomState.WAITING,

        'room_members': {},

        'pending': 99,
        'timer': None,

        'history': [],
        'current_round': 0
    }
}

USER_ROOM_MAP = {}