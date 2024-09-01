import paho.mqtt.client as mqtt_client
from rotator import rot
import time

globalName = "myGS/"


def set_rothost(host):
    print(f"The rotator host is now {host}")
    rot.host = host


def set_rotport(port):
    print(f"Rot Port -> {port}")
    rot.port = int(port)


def set_rotmodel(model):
    print(f"Rot model -> {model}")
    rot.model = model


def set_rotdev(dev):
    print(f"Rot dev -> {dev}")
    rot.device = dev


def set_rotsspeed(sspeed):
    print(f"Rot serial speed -> {sspeed}")
    rot.sspeed = sspeed


def set_rotselect(preset):
    if not preset:
        print("No preset selected, using given parameters")
        try:
            rot.end()
            # WARN: this is just for testing. Don't leave this here! 
        except Exception:
            print('No daemon to end')
        try:
            rot.start_daemon()
        except Exception:
            print('Could not start daemon')


    else:
        print(f"Rotator Preset -> {preset}")


def set_newpreset(preset):
    print(f"New preset:\n\t{preset}")


mqttTopics = {
    # Radio
    f"{globalName}radio/freq": "freq",
    f"{globalName}radio/bw": "bw",
    f"{globalName}radio/cr": "cr",
    f"{globalName}radio/plen": "plen",
    f"{globalName}radio/sf": "sf",
    f"{globalName}radio/txpwr": "txpwr",
    f"{globalName}radio/lnag": "lnag",
    f"{globalName}radio/chksum": "chksum",
    f"{globalName}radio/ackd": "ackd",
    f"{globalName}radio/ackw": "ackw",
    f"{globalName}radio/rxto": "rxto",
    # Rotator
    f"{globalName}rot/daemon": "daemon",
    f"{globalName}rot/host": set_rothost,
    f"{globalName}rot/port": set_rotport,
    f"{globalName}rot/dev": set_rotdev,
    f"{globalName}rot/sspeed": set_rotsspeed,
    f"{globalName}rot/model": set_rotmodel,
    f"{globalName}rot/select": set_rotselect,
    f"{globalName}rot/newpreset": set_newpreset,
}

# Define the MQTT topics
pub_topics = [
    f"{globalName}msg/telemetry",
    f"{globalName}msg/payload",
    f"{globalName}msg/reply",
]

# Define the MQTT broker address and port
broker_address = "10.42.0.236"
# broker_address = "test.mosquitto.org"  # "localhost"
broker_port = 1883


# Define the on_connect callback function


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subscribe to all topics
    for topic in mqttTopics:
        print(topic)
        client.subscribe(topic)


# Define the on_message callback function
# def on_message(client, userdata, msg):
#     print(f"Received message on {msg.topic}: {msg.payload.decode()}")


# Initialize the MQTT client
mqttC = mqtt_client.Client()

# Assign the callback functions
mqttC.on_connect = on_connect
# mqttC.on_message = on_message

# Connect to the broker
# mqttC.connect(broker_address, broker_port)

# Start the MQTT client loop
# mqttC.loop_start()

# Publish messages to the topics
if __name__ == "__main__":
    try:
        while True:
            cmd = input("user cmd:").split()
            if len(cmd) > 1:
                topic, value = cmd
            else:
                continue

            if topic not in pub_topics:
                print("Topic not available")
            print(mqttC.publish(globalName + topic, value))
            """
            for i, topic in enumerate(topics):
                message = f"Message from Program 2 to {topic}"
                mqttC.publish(topic, message)
                print(f"Published message to {topic}: {message}")
                time.sleep(1)
            time.sleep(5)  # Delay between each round of publishing
            """
    except KeyboardInterrupt:
        mqttC.loop_stop()
        mqttC.disconnect()

    # Stop the MQTT client loop and disconnect
    mqttC.loop_stop()
    mqttC.disconnect()
