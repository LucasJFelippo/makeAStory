from flask import Flask, render_template


app = Flask(__name__)


@app.route('/')
def lobby():
    return render_template('lobby.html')


@app.route('/r')
def chat():
    return render_template('room.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)