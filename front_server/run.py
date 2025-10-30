from src.main import create_app
import logging

logging.getLogger('werkzeug').setLevel(logging.ERROR)

if __name__ == "__main__":
    app, socketio = create_app()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)