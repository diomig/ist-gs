import paho.mqtt.client as mqtt_client

from radio import radio
from rotator import rot

globalName = "myGS/"

""" Radio Parameters
"""


def set_freq(val):
    freq = float(val)
    print(f"Carrier frequency -> {val}")
    radio.frequency_mhz = freq / 1e6


def set_bandwidth(val):
    bw = float(val)
    print(f"Bandwidth -> {val}")
    radio.signal_bandwidth = bw


def set_code_rate(val):
    cr = int(val)
    print(f"Code Rate -> 4/{val}")
    radio.coding_rate = cr


def set_preamble_length(val):
    plen = int(val)
    print(f"Preamble Length -> {val}")
    radio.preamble_length = plen


def set_spreading_factor(val):
    sf = int(val)
    print(f"SF -> {val}")
    radio.spreading_factor = sf


def set_tx_power(val):
    txpwr = float(val)
    print(f"Tx Power -> {val}")
    radio.tx_power = txpwr


def set_lna_gain(val):
    lnag = int(float(val))
    print(f"LAN Gain -> {val}")
    radio.lna_boost = lnag


def set_checksum(val):
    state = "ON" if val.lower() == "true" else "OFF"
    print(f"Checksum {state}")
    # TODO: complete this


def set_ack_delay(val):
    delay = float(val)
    print(f"ACK Delay -> {val}")
    radio.ack_delay = delay


def set_ack_wait(val):
    wait = float(val)
    print(f"ACK Wait -> {val}")
    radio.ack_wait = wait


def set_rx_timeout(val):
    rxto = float(val)
    print(f"Rx Timeout -> {val}")
    radio.receive_timeout = rxto


""" Rotator Parameters
"""


def set_rotdaemon(daemon):
    print(f"Daemon set to {daemon}")


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
            print("No daemon to end")
        try:
            rot.start_daemon()
        except Exception:
            print("Could not start daemon")

    else:
        print(f"Rotator Preset -> {preset}")


def set_newpreset(preset):
    print(f"New preset:\n\t{preset}")


def send_cmd(cmd):
    print(f'Tx command: {cmd}')
    radio.send(cmd)


mqttTopics = {
    # Radio
    f"{globalName}radio/freq": set_freq,  # "freq",
    f"{globalName}radio/bw": set_bandwidth,
    f"{globalName}radio/cr": set_code_rate,
    f"{globalName}radio/plen": set_preamble_length,
    f"{globalName}radio/sf": set_spreading_factor,  # "sf",
    f"{globalName}radio/txpwr": set_tx_power,
    f"{globalName}radio/lnag": set_lna_gain,
    f"{globalName}radio/chksum": set_checksum,
    f"{globalName}radio/ackd": set_ack_delay,
    f"{globalName}radio/ackw": set_ack_wait,
    f"{globalName}radio/rxto": set_rx_timeout,
    # Rotator
    f"{globalName}rot/daemon": set_rotdaemon,
    f"{globalName}rot/host": set_rothost,
    f"{globalName}rot/port": set_rotport,
    f"{globalName}rot/dev": set_rotdev,
    f"{globalName}rot/sspeed": set_rotsspeed,
    f"{globalName}rot/model": set_rotmodel,
    f"{globalName}rot/select": set_rotselect,
    f"{globalName}rot/newpreset": set_newpreset,
    # Messaging
    f"{globalName}msg/cmd": send_cmd,
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
