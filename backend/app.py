"""
Smart Home Backend
- Souscrit au broker MQTT (topic home/sensors/urm09)
- Persiste chaque lecture dans SQLite
- Expose une API REST + WebSocket temps réel
- Sert le dashboard HTML sur /
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

# ── App ────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']        = 'sqlite:///smart_home.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']                     = 'smarthome-secret-key'

db       = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

# ── Configuration MQTT ─────────────────────────────────────────────────────────
MQTT_BROKER = 'localhost'
MQTT_PORT   = 1883
MQTT_TOPIC  = 'home/sensors/urm09'


# ── Modèle ─────────────────────────────────────────────────────────────────────
class SensorReading(db.Model):
    __tablename__ = 'sensor_readings'

    id         = db.Column(db.Integer,  primary_key=True)
    distance   = db.Column(db.Float,   nullable=False)
    led_active = db.Column(db.Boolean, default=False)
    presence   = db.Column(db.Boolean, default=False)
    uptime     = db.Column(db.Integer, default=0)
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            'id':         self.id,
            'distance':   round(self.distance, 1),
            'led_active': self.led_active,
            'presence':   self.presence,
            'uptime':     self.uptime,
            'timestamp':  self.timestamp.isoformat(),
        }


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route('/')
def dashboard():
    return render_template('index.html')


@app.route('/api/readings')
def get_readings():
    limit = request.args.get('limit', 100, type=int)
    rows  = (
        SensorReading.query
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
        .all()
    )
    return jsonify([r.to_dict() for r in reversed(rows)])


@app.route('/api/readings/latest')
def get_latest():
    row = SensorReading.query.order_by(SensorReading.timestamp.desc()).first()
    if row:
        return jsonify(row.to_dict())
    return jsonify(None), 404


@app.route('/api/stats')
def get_stats():
    total      = SensorReading.query.count()
    detections = SensorReading.query.filter_by(presence=True).count()
    avg_dist   = db.session.query(func.avg(SensorReading.distance)).scalar()

    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent       = SensorReading.query.filter(SensorReading.timestamp >= one_hour_ago).count()
    recent_det   = SensorReading.query.filter(
        SensorReading.timestamp >= one_hour_ago,
        SensorReading.presence  == True,
    ).count()

    return jsonify({
        'total_readings':       total,
        'presence_detections':  detections,
        'detection_rate':       round(detections / total * 100, 1) if total else 0,
        'average_distance':     round(avg_dist, 1) if avg_dist else 0,
        'last_hour_readings':   recent,
        'last_hour_detections': recent_det,
    })


@app.route('/api/readings/history')
def get_history():
    minutes = request.args.get('minutes', 10, type=int)
    since   = datetime.utcnow() - timedelta(minutes=minutes)
    rows    = (
        SensorReading.query
        .filter(SensorReading.timestamp >= since)
        .order_by(SensorReading.timestamp.asc())
        .all()
    )
    return jsonify([r.to_dict() for r in rows])


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})


# ── MQTT ───────────────────────────────────────────────────────────────────────
def on_mqtt_connect(client, _ud, _flags, rc):
    if rc == 0:
        print(f'[MQTT] Connecté — abonnement à {MQTT_TOPIC}')
        client.subscribe(MQTT_TOPIC)
    else:
        print(f'[MQTT] Erreur connexion, rc={rc}')


def on_mqtt_message(client, _ud, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))

        with app.app_context():
            reading = SensorReading(
                distance   = float(data['distance']),
                led_active = bool(data.get('led',      False)),
                presence   = bool(data.get('presence', False)),
                uptime     = int(data.get('uptime',    0)),
            )
            db.session.add(reading)
            db.session.commit()

            socketio.emit('sensor_update', reading.to_dict())

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f'[MQTT] Message invalide : {exc}')


def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_forever()
        except Exception as exc:
            import time
            print(f'[MQTT] Connexion échouée : {exc} — retry dans 5s')
            time.sleep(5)


# ── Démarrage ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print('[DB] Base de données prête (smart_home.db)')

    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()
    print('[MQTT] Thread client démarré')

    print('[SERVER] Dashboard → http://localhost:5000')
    socketio.run(app, host='0.0.0.0', port=5000, debug=False,
                 allow_unsafe_werkzeug=True)
