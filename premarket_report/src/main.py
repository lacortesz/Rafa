# app.py
from flask import Flask
from flask_socketio import SocketIO

from routes.dashboard import bp as dashboard_bp
from routes.chart import bp as chart_bp
from utils.kafka_consumer import start_consumer

app = Flask(__name__)
socketio = SocketIO(app)

app.register_blueprint(dashboard_bp)
app.register_blueprint(chart_bp) 

start_consumer(socketio)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
