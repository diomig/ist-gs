"""
"""

import json
import struct
import time

import decoder
from lib.logs import unpack_beacon
from lib.radio_utils import headers
from lib.radio_utils.commands import (_pack, _unpack, commands,
                                      super_secret_code)
from lib.radio_utils.disk_buffered_message import DiskBufferedMessage
from shell_utils import bold, normal, red

try:
    import calendar

    HAS_CALENDAR = True
except Exception:
    HAS_CALENDAR = False


commands_by_name = {
    commands[cb]["name"]: {
        "bytes": cb,
        "will_respond": commands[cb]["will_respond"],
        "has_args": commands[cb]["has_args"],
    }
    for cb in commands.keys()
}


async def send_command(
    radio,
    command_bytes,
    args,
    will_respond,
    max_rx_fails=30,
    debug=False,
    args_are_bytes=False,
):
    success = False
    response = None
    header = None
    if not args_are_bytes:
        args = bytes(args, "utf-8")
    msg = bytes([headers.COMMAND]) + super_secret_code + command_bytes + args
    if await radio.send_with_ack(msg, debug=debug):
        if debug:
            print("Successfully sent command")
        if will_respond:
            if debug:
                print("Waiting for response")
            header, response = await wait_for_message(
                radio, max_rx_fails=max_rx_fails, debug=debug
            )
            if debug:
                print_message(header, response)
            if header is not None:
                success = True
            else:
                success = False
        else:
            success = True
    else:
        if debug:
            print("Failed to send command")
        success = False
    return success, header, response


async def move_file(radio, source_path, destination_path, debug=False):
    arg_string = json.dumps([source_path, destination_path])
    success, _, response = await send_command(
        radio,
        commands_by_name["MOVE_FILE"]["bytes"],
        arg_string,
        commands_by_name["MOVE_FILE"]["will_respond"],
        debug=debug,
    )

    if "success" in str(response).lower():
        success &= True
    else:
        success &= False

    if debug:
        if success:
            print(f"{bold}MOVE_FILE Response:{normal} {decode_message(response)}")
        else:
            print(f"{bold}MOVE_FILE Response:{normal} {red}FAILED{normal}")

    return success


async def request_file(radio, path, debug=False):
    success, header, response = await send_command(
        radio,
        commands_by_name["REQUEST_FILE"]["bytes"],
        path,
        commands_by_name["REQUEST_FILE"]["will_respond"],
        debug=debug,
        max_rx_fails=40,
    )

    if header == headers.DEFAULT:
        success &= (
            False  # this is not a DiskBufferedMessage - an error must have occurred
        )

    if debug:
        if success:
            print(
                f"{bold}REQUEST_FILE:{normal} {path}\n\nContents:\n{decode_message(response)}"
            )
        else:
            print(f"{bold}REQUEST_FILE:{normal} {path} {red}FAILED{normal}")

    return success, header, response


async def upload_file(radio, local_path, satellite_path, debug=False):
    msg = DiskBufferedMessage(local_path)

    success = await send_message(radio, msg, debug=debug, packet_delay=0.1)

    if success:
        success &= await move_file(
            radio, "/sd/disk_buffered_message", satellite_path, debug=debug
        )
    return success


async def request_beacon(radio, debug=False):
    success, header, response = await send_command(
        radio,
        commands_by_name["REQUEST_BEACON"]["bytes"],
        "",
        commands_by_name["REQUEST_BEACON"]["will_respond"],
        debug=debug,
    )

    if success and header == headers.BEACON:
        return True, beacon_str(response)
    else:
        return False, None


async def set_time(radio, unix_time=None, debug=False):
    """Update the real time clock on the satellite using
    either a given value or the system time"""
    if unix_time is None:
        if HAS_CALENDAR:
            unix_time = calendar.timegm(time.gmtime())
        else:
            print("GMT unavailable - using local time")
            unix_time = time.mktime(time.localtime())

    if debug:
        print(f"Updating time to {unix_time}")

    args = struct.pack("i", unix_time)

    success, _, _ = await send_command(
        radio,
        commands_by_name["SET_RTC_UTIME"]["bytes"],
        args,
        commands_by_name["SET_RTC_UTIME"]["will_respond"],
        debug=debug,
        args_are_bytes=True,
    )

    return success


async def get_time(radio, debug=False):
    success, header, response = await send_command(
        radio,
        commands_by_name["GET_RTC_UTIME"]["bytes"],
        "",
        commands_by_name["GET_RTC_UTIME"]["will_respond"],
        debug=debug,
    )

    if success and header == headers.DEFAULT:
        sat_time = struct.unpack("i", response)[0]
        return True, sat_time
    else:
        return False, None


async def receive(rfm9x, with_ack=False, debug=False):
    """Recieve a packet.  Returns None if no packet was received.
    Otherwise returns (header, payload)"""

    packet = rfm9x.receive(with_ack=with_ack, with_header=True, debug=debug)
    if packet is None:
        return None
    # print(packet[4])
    # print(packet)
    return packet[0:5], packet[5:]


async def send_message(radio, msg, debug=False, packet_delay=0):
    success = True
    while True:
        packet, with_ack = msg.packet()

        if debug:
            debug_packet = str(packet)[:20] + \
                "...." if len(packet) > 23 else packet
            print(f"Sending packet: {debug_packet}, with_ack: {with_ack}")

        if with_ack:
            got_ack = await radio.send_with_ack(packet, debug=True)
            if got_ack:
                msg.ack()
            else:
                success = False
                break
        else:
            await radio.send(packet, keep_listening=True)

        if msg.done():
            break

        time.sleep(packet_delay)

    return success


class _data:

    def __init__(self):
        self.msg = bytes([])
        self.msg_last = bytes([])
        self.cmsg = bytes([])
        self.cmsg_last = bytes([])


storage = []


def parse_message(raw):
    try:
        data = decoder.Prometheus.from_bytes(raw)
    except Exception:
        print("WRONG DATA STRUCTURE!!!")
        return
    id = data.packet_id
    if id == 0x00:
        parse_telemtry(data)
    else:
        print("IMAGE SEGMENT ", id, "of", data.payload.total)
        # print(data.payload.segment)
        rebuid_image(data, storage)


def parse_telemtry(data):
    imu = data.payload.imu
    print("ACCEL X: %7.4f" % imu.accel_x, end="\t\t")
    print("ACCEL Y: %7.4f" % imu.accel_y, end="\t\t")
    print("ACCEL Z: %7.4f" % imu.accel_z)

    print("GYRO  X: %7.4f" % imu.gyro_x, end="\t\t")
    print("GYRO  Y: %7.4f" % imu.gyro_y, end="\t\t")
    print("GYRO  Z: %7.4f" % imu.gyro_z)

    print("MAG   X: %7.4f" % imu.mag_x, end="\t\t")
    print("MAG   Y: %7.4f" % imu.mag_y, end="\t\t")
    print("MAG   Z: %7.4f" % imu.mag_z)

    print("TEMP: %7.4f" % imu.temp)
    print()

    sun_sensor = data.payload.sun_sensor
    print("SUN X+: ", sun_sensor.sun_xp, "SUN X-: ", sun_sensor.sun_xn)
    print("SUN Y+: ", sun_sensor.sun_yp, "SUN Y-: ", sun_sensor.sun_yn)
    print("SUN Z+: ", sun_sensor.sun_zp, "SUN Z-: ", sun_sensor.sun_zn)
    print()

    print("Battery Voltage: ", data.payload.vbatt, "V")
    print("CPU Temp: ", data.payload.cpu_temp, "deg C")
    print()


def rebuid_image(data, storage):
    id = data.packet_id
    segment = data.payload.segment
    total = 19
    summary = [stg["id"] for stg in storage]
    if id not in summary:
        storage.append({"id": id, "seg": segment})
    print(summary)

    if len(storage) < total:
        return
    storage = sorted(storage, key=lambda d: d["id"])
    print("GOT THEM ALL!!!")
    image = b"".join([stg["seg"] for stg in storage])

    with open("image.png", "wb") as file:
        file.write(image)


async def wait_for_message(radio, max_rx_fails=100000, debug=False):
    data = _data()

    rx_fails = 0
    while True:
        res = await receive(radio, debug=debug)

        if res is None:
            rx_fails += 1
            if rx_fails > max_rx_fails:
                if debug:
                    print("wait_for_message: max_rx_fails Hit")
                return None, data.msg + data.cmsg
            else:
                continue
        else:
            rx_fails = 0

        header, payload = res
        # parse_message(header + payload)
        '''
        oh = header[4]
        # print(oh)
        if oh == headers.DEFAULT or oh == headers.BEACON:
            return oh, payload
        elif (
            oh == headers.MEMORY_BUFFERED_START
            or oh == headers.MEMORY_BUFFERED_MID
            or oh == headers.MEMORY_BUFFERED_END
        ):
            handle_memory_buffered(oh, data, payload)
            if oh == headers.MEMORY_BUFFERED_END:
                return headers.MEMORY_BUFFERED_START, data.msg

        elif (
            oh == headers.DISK_BUFFERED_START
            or oh == headers.DISK_BUFFERED_MID
            or oh == headers.DISK_BUFFERED_END
        ):
            handle_disk_buffered(oh, data, payload)
            if oh == headers.DISK_BUFFERED_END:
                return headers.DISK_BUFFERED_START, data.cmsg
        elif (
            oh == headers.IMAGE_START
            or oh == headers.IMAGE_MID
            or oh == headers.IMAGE_END
        ):
            handle_image(oh, data, payload)
            if oh == headers.IMAGE_END:
                return headers.IMAGE_START, data.cmsg
        else:
            print(f"Unrecognized header {oh}")
            return oh, payload
        '''
        print('Rx: ', res)
        return header, payload

def print_message(header, message):
    if header == headers.DEFAULT:
        print(f"Default: {decode_message(message)}")
    # elif header == headers.BEACON:
    #    print(beacon_str(message))
    # elif header == headers.MEMORY_BUFFERED_START or header == headers.DISK_BUFFERED_START:
    #    print(f"Buffered:\n")
    #    decode_message(message)

    else:
        print(f"Header {header} unknown: {decode_message(message)}")


def decode_message(message):
    try:
        return message.decode(encoding="utf-8", errors="strict")
    except UnicodeDecodeError:
        return message.hex(" ")


def beacon_str(beacon):
    beacon_dict = unpack_beacon(beacon)
    bs = f"\n{bold}Beacon:{normal}"
    for bk in beacon_dict:
        bv = beacon_dict[bk]
        if isinstance(bv, float):
            bvstr = f"{bv:.4}"
        else:
            bvstr = str(bv)
        bs += f"\t{bk:.<35} {bvstr}\n"
    return bs


def handle_memory_buffered(header, data, payload):
    if header == headers.MEMORY_BUFFERED_START:
        data.msg_last = payload
        data.msg = payload
    else:
        if payload != data.msg_last:
            data.msg += payload
        else:
            print("Repeated payload")

    if header == headers.MEMORY_BUFFERED_END:
        data.msg_last = bytes([])


def handle_disk_buffered(header, data, response):
    if header == headers.DISK_BUFFERED_START:
        data.cmsg = response
        data.cmsg_last = response
    else:
        if response != data.cmsg_last:
            data.cmsg += response
        else:
            print("Repeated payload")
        data.cmsg_last = response

    if header == headers.DISK_BUFFERED_END:
        data.cmsg_last = bytes([])


def handle_image(header, data, response):
    if header == headers.DISK_BUFFERED_START:
        data.cmsg = response
        data.cmsg_last = response
        try:
            with open("image_test.jpeg", "wb") as fd:
                fd.write(response)
        except Exception as e:
            print(f"failed to create file: {e}")
    else:
        if response != data.cmsg_last:
            data.cmsg += response
            try:
                with open("image_test.jpeg", "ab") as fd:
                    fd.write(response)
            except Exception as e:
                print(f"failed to write to image: {e}")
        else:
            print("Repeated payload")
        data.cmsg_last = response

    if header == headers.DISK_BUFFERED_END:
        data.cmsg_last = bytes([])
