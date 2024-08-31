from rotator import Rotator
from MQTT import mqttC, mqttTopics, pub_topics, globalName


def on_message(client, userdata, msg):
    print(f"Received message on {msg.topic}: {msg.payload.decode()}")


# Define the MQTT broker address and port
broker_address = "10.42.0.236"
# broker_address = "test.mosquitto.org"  # "localhost"
broker_port = 1883

mqttC.on_message = on_message
mqttC.connect(broker_address, broker_port)
mqttC.loop_start()

if __name__ == '__main__':
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

    except KeyboardInterrupt:
        mqttC.loop_stop()
        mqttC.disconnect()

    # Stop the MQTT client loop and disconnect
    mqttC.loop_stop()
    mqttC.disconnect()


