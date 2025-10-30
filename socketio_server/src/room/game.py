from src.data import ROOMS, RoomState


def start_game(room_id):
    print("GAME START")
    start_round(room_id)

def start_round(room_id):
    room = ROOMS[room_id]
    room['room_state'] = RoomState.SNIPPETING
    room['pending'] = len(room['room_members'])
    # TODO: Implement timming

def end_round(room_id):
    room = ROOMS[room_id]
    room['room_state'] = RoomState.READING
    room['pending'] = len(room['room_members'])