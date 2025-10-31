from enum import Enum
from string import Template


GPT_ENTRY_PROMPT = '''We are playing a collaborative storytelling game, in this game you and other players will create a compelling and cool story together, and in this game you are the game master. The game are played in rounds, each round each player will write a short story snippet, your task is to mix together all the story snippets of the players, in a short story. After that another round start and again the players send another snippets so we can continue the story.\n\n The story snippets will be at maximum 100 characters long, and your responses must be 1-2 paragraphs of lore (you can write either 1 or 2 paragraphs, at your discretion), and have at maximum 1000 characters long. Try to be as creative as possible, but keeping the cohesion between the snippets and mainly the rounds. You don't have to use all snippets ideas at once, if you judge a idea is a good card to keep for the future you can, but you must bring it back as soon as it fits the story, a idea can be 'held' for at most 5 rounds.'''

GPT_SNIPPETS_TEMPLATE = Template('''Round $cround snippets:

$snippets

Now continue the story with this new snippets.''')


class RoomState(Enum):
    WAITING = 0
    SNIPPETING = 1
    RESPONSE = 2
    READING = 4

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
        'history_parsed': [],
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
        'history_parsed': [{
                'role': 'developer',
                'content': GPT_ENTRY_PROMPT
            }],
        'current_round': 0
    }
}

USER_ROOM_MAP = {}


# Config

MAX_ROOM_SIZE = 5

MAX_SNIPPET_SIZE = 100   # in characters


'''
Custom Events Schema

connect_ack: server -> client
    Acknowledgement that client connected successfully (since on_connect can't return a ack)

join_room: client -> server
    Client ask to join a room
    
    Params:
        room_id: int
    
    Ack:
        status: str
            - ok
            - error
        msg: str (only set if status is error)
            - full               if the room is full
            - special message    if user try to join a room that not exist


start_game: client -> server
    One of the player clicked to start the game

    Ack:
        status: str
            - error
        msg: str (only set if status is error)
            - not in room        user is not in a room
            - room not waiting   room is not in waiting state

game_started: server -> client
    Broadcast that game have started to all users

    Params:
        triggerer: str
            - user_id


round_started: server -> client
    Broadcast that round have started to all users

    Params:
        triggerer: str
            - user_id          if a user have started the round
            - game_start       if it was triggered by game start event


story_snippet: client -> server
    Player submitted a story snippet

    Params:
        snippet: str

    Ack:
        status: str
            - ok                 snippet received, but didn't cause round to end
            - error
        msg: str (only set if status is error)
            - not in room        user is not in a room
            - room not reading   room is not in reading state
            - size limit         snippet bigger than MAX_SNIPPET_SIZE

ai_response: server -> client
    Response from the AIs

    Params:
        type: str
            - ai_response
        story: str
        image_url: str
        song_url: str
'''