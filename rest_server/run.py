from src.main import create_app
from models import db, GameRoom
import logging

logging.getLogger('werkzeug').setLevel(logging.ERROR)

if __name__ == "__main__":
    app, socketio = create_app()
    with app.app_context():
        db.create_all()
    if not app.debug:
            try:
                print("Limpando salas 'IN_PROGRESS' de sessões anteriores...")
                stuck_rooms = GameRoom.query.filter_by(status='IN_PROGRESS').all()
                
                if stuck_rooms:
                    print(f"   Encontradas {len(stuck_rooms)} salas presas. Resetando...")
                    for room in stuck_rooms:
                        room.status = 'LOBBY'
                        room.participants = []
                    
                    db.session.commit()
                    print("   ...Salas resetadas com sucesso.")
                else:
                    print("   Nenhuma sala presa encontrada.")

            except Exception as e:
                print(f"ERRO ao tentar limpar salas presas: {e}")
                db.session.rollback()

    socketio.run(app, host='0.0.0.0', port=5000, debug=True)