from src.main import create_app
from models import db
import logging

logging.getLogger('werkzeug').setLevel(logging.ERROR)

if __name__ == "__main__":
    app, socketio = create_app()
    with app.app_context():
        db.create_all()

    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)