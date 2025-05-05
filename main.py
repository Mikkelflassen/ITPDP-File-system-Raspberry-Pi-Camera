import time
import random
from flask import Flask, request, render_template, g, jsonify, redirect, url_for
from paho.mqtt import client as mqtt_client
from db_handler import TrackerDB

# MQTT setup
broker = 'broker.emqx.io'
port = 1883
topic = "au-itpdp-group3-2025"
client_id = f'publish-{random.randint(0, 1000)}'

# Connect function
def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

# Publish message function
def publish(client, msg):
    time.sleep(1)
    result = client.publish(topic, msg)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")

# Flask setup
app = Flask(__name__)

# Routes below
@app.route('/')
def index():
    return render_template('front_page.html')

@app.route('/direction/<string:direction>', methods=['GET'])
def drive(direction):
    print(direction)
    client = connect_mqtt()
    client.loop_start()
    publish(client, direction)
    client.loop_stop()
    return redirect(url_for('index'))

@app.route('/video/upload', methods=['POST'])
def upload_video():
    print('uploading video')