# from gs_commands import *
# from shell_utils import *
import time

import gs_commands as gc
import shell_utils as su
from MQTT import globalName, mqttC


async def send_command_task(radio, command_bytes, args, will_respond, debug=False):
    success, header, response = await gc.send_command(
        radio, command_bytes, args, will_respond, debug=debug
    )
    if success:
        print("Command successful")
        if header is not None and response is not None:
            gc.print_message(header, response)
    else:
        print("Command failed")


async def get_time_task(radio, debug=False):
    success, sat_time = await gc.get_time(radio, debug=debug)
    if success:
        print(f"Time = {sat_time}")
    else:
        print("Command failed")


async def read_loop(radio, debug=False):

    while True:
        header, message = await gc.wait_for_message(radio, debug=debug)
        if header or (message and len(message) > 0):
            gc.print_message(header, message)
            mqttC.publish(f"{globalName}msg/payload", header + message)
            packetRSSI = radio.last_rssi * 16 / 15 - 164
            mqttC.publish(f"{globalName}msg/rssi", packetRSSI)
            print(f"\nSNR: {radio._read_u8(0x19)}\n\n\n")


def human_time_stamp():
    """Returns a human readable time stamp in the format:
    'year.month.day hour:min'
    Gets the local time."""
    t = time.localtime()
    return f"{t.tm_year:4}.{t.tm_mon:02}.{t.tm_mday:02}.{t.tm_hour:02}:{t.tm_min:02}:{t.tm_sec:02}"


def timestamped_log_print(str, printcolor=su.normal, logname=""):
    """
    Timestamp, print to stdout and log str to a file
    """
    timestamp = human_time_stamp()

    print(f"[{su.yellow}{timestamp}{su.normal}]\t" + f"{printcolor}{str}{su.normal}")

    if logname is not None and not logname == "":
        try:
            with open(logname, "a") as f:
                f.write(f"[{timestamp}]\t" + f"{str}" + "\n")
        except OSError as e:
            print(e)


async def get_beacon(radio, debug=False, logname=""):
    timestamped_log_print("Requesting beacon...", logname=logname)
    success, bs = await gc.request_beacon(radio, debug=debug)
    if success:
        timestamped_log_print(
            "Successful beacon request", printcolor=su.green, logname=logname
        )
        timestamped_log_print(bs, logname=logname)
    else:
        timestamped_log_print(
            "Failed beacon request", printcolor=su.red, logname=logname
        )
