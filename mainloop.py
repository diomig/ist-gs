import gs_setup as setup
import shell_utils as su
from MQTT import globalName, mqttC, mqttTopics, pub_topics
from rotator import rot
import gs_shell

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    if callable(mqttTopics[topic]):
        mqttTopics[topic](payload)
    else:
        print(f"Received message on {topic}: {payload}")


def radio_setup():
    spi, cs, reset = setup.init_spi()
    radio = setup.initialize_rfm9x(spi, cs, reset)
    print("Radio Initialized")

    su.print_radio_configuration(radio)


# Define the MQTT broker address and port
broker_address = "10.42.0.236"
# broker_address = "test.mosquitto.org"  # "localhost"
broker_port = 1883

mqttC.on_message = on_message
mqttC.connect(broker_address, broker_port)
mqttC.loop_start()


if __name__ == "__main__":
    try:
        radio = radio_setup()
        gs_shell.print_help()
        gs_shell.gs_shell_main_loop(radio)
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
