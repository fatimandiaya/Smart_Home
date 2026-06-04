#!/usr/bin/env python3
"""
Pont Serial -> MQTT
Lit les données JSON de l'Arduino via USB et les publie sur le broker MQTT.

Usage:
    python serial_mqtt_bridge.py          # utilise SERIAL_PORT défini ci-dessous
    python serial_mqtt_bridge.py COM4     # spécifie le port en argument
"""

import serial
import serial.tools.list_ports
import paho.mqtt.client as mqtt
import json
import time
import logging
import sys

# ── Configuration ─────────────────────────────────────────────────────────────
SERIAL_PORT     = 'COM3'       # Windows: COM3, COM4… | Linux: /dev/ttyACM0
BAUD_RATE       = 9600
MQTT_BROKER     = 'localhost'
MQTT_PORT       = 1883
MQTT_TOPIC      = 'home/sensors/urm09'
RECONNECT_DELAY = 5
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger(__name__)


def list_ports():
    ports = serial.tools.list_ports.comports()
    if not ports:
        log.warning("Aucun port série détecté.")
    else:
        log.info("Ports série disponibles :")
        for p in ports:
            log.info("  %s – %s", p.device, p.description)


def build_mqtt_client() -> mqtt.Client:
    client = mqtt.Client()

    def on_connect(c, _ud, _flags, rc):
        if rc == 0:
            log.info("[MQTT] Connecté au broker %s:%s", MQTT_BROKER, MQTT_PORT)
        else:
            log.error("[MQTT] Connexion refusée, code %s", rc)

    def on_disconnect(c, _ud, rc):
        if rc != 0:
            log.warning("[MQTT] Déconnexion inattendue, code %s", rc)

    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_start()
            return client
        except Exception as exc:
            log.error("[MQTT] Impossible de se connecter : %s", exc)
            log.info("Nouvelle tentative dans %ss…", RECONNECT_DELAY)
            time.sleep(RECONNECT_DELAY)


def run():
    log.info("=== Pont Serial → MQTT démarré ===")
    list_ports()

    mqtt_client = build_mqtt_client()
    count = 0

    while True:
        try:
            log.info("Ouverture du port %s @ %s baud…", SERIAL_PORT, BAUD_RATE)
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                log.info("Port série ouvert : %s", SERIAL_PORT)
                ser.reset_input_buffer()

                while True:
                    raw = ser.readline().decode('utf-8', errors='ignore').strip()

                    if not raw.startswith('{'):
                        continue

                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        log.debug("Ligne ignorée (JSON invalide) : %s", raw)
                        continue

                    if 'distance' not in data:
                        continue

                    result = mqtt_client.publish(MQTT_TOPIC, json.dumps(data), qos=1)

                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        count += 1
                        log.info(
                            "[#%d] dist=%.1fcm | led=%s | présence=%s | uptime=%ss",
                            count,
                            data['distance'],
                            'ON'  if data.get('led')      else 'off',
                            'OUI' if data.get('presence') else 'non',
                            data.get('uptime', '?'),
                        )
                    else:
                        log.warning("Publication MQTT échouée, rc=%s", result.rc)

        except serial.SerialException as exc:
            log.error("Erreur port série : %s", exc)
            log.info("Nouvelle tentative dans %ss…", RECONNECT_DELAY)
            time.sleep(RECONNECT_DELAY)

        except KeyboardInterrupt:
            log.info("Arrêt demandé.")
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            sys.exit(0)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        SERIAL_PORT = sys.argv[1]
        log.info("Port série (argument) : %s", SERIAL_PORT)
    run()
