import socket
import subprocess
import time
from sys import argv
from warnings import warn

import yaml

from shell_utils import bold, normal, red, yellow

with open("lib/configuration/rot_config.yaml", "r") as file:
    config = yaml.safe_load(file)


def is_float(val):
    try:
        float(val)
        return True
    except ValueError:
        return False


class Rotator:
    def __init__(
        self,
        rotconfig=config,
        verbose=False,
    ):
        if len(argv) < 2:
            rotname = rotconfig["select"]
        else:
            rotname = argv[1]
        config = rotconfig[rotname]
        attributes = ["daemoncmd", "host", "port", "model", "device", "sspeed"]
        for attr in attributes:
            setattr(self, attr, config[attr] if attr in config else None)
        self.verbose = verbose

        self.check_config()
        print(self.cmd_options())

        self.start_daemon()
        # TODO: replace sleep for a non blocking wait
        time.sleep(3)
        if self.host and self.port:
            self.open_socket()

    def check_config(self):
        if self.daemoncmd is None:
            raise Exception(
                f"""{red}Daemon command/path not specified\
            {normal}"""
            )
        if self.model is None:
            warn(f"{yellow}No model specified. Using dummie model{normal}")
        if self.host is None:
            self.host = "localhost"
            warn(
                f"""{yellow}
            No address specified. Using default
            {bold}(localhost/127.0.0.1)
            {normal}"""
            )
        if self.port is None:
            self.port = 4533
            warn(
                f"""{yellow}
            No port specified, using default
            {bold}({self.port})
            {normal}"""
            )

    def cmd_options(self):
        opts = [
            self.daemoncmd,  # "rotctld",
            f"-m {self.model}" if self.model else "",
            f"-T {self.host}" if self.host else "",
            f"-t {self.port}" if self.port else "",
            f"-r {self.device}" if self.device else "",
            f"-s {self.sspeed}" if self.sspeed else "",
            "-vvvv" if self.verbose else "",
        ]

        return " ".join(opts).split()

    def start_daemon(self):
        self.daemon = subprocess.Popen(self.cmd_options())

    def terminate_daemon(self):
        self.daemon.terminate()
        self.daemon.wait()

    def open_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def close_socket(self):
        self.socket.close()

    def command(self, cmd: str):
        buffsize = 20
        self.socket.send((cmd + "\x0a").encode())
        return self.socket.recv(buffsize).decode()

    def get_pos(self):
        return self.command("p").split()

    def set_pos(self, az, el):
        if not (is_float(az) and is_float(el)):
            return f"{yellow}Numeric values only!{normal}"
        cmd = f"P {az} {el}\x0a"
        return self.command(cmd)

    def end(self):
        self.command("q")
        self.close_socket()
        self.terminate_daemon()
        print("\nRotator Terminated")


if __name__ == "__main__":
    rot = Rotator(config, verbose=False)

    try:
        while True:
            prompt = input("--> ")

            if prompt in ["getpos", "g", "p"]:
                az, el = rot.get_pos()
                print(f"AZ: {az}; EL: {el}")
            elif prompt in ["setpos", "s", "P"]:
                print(rot.set_pos(input("az: "), input("el: ")))
            elif prompt == "q":
                rot.end()
                break
    except (KeyboardInterrupt, subprocess.TimeoutExpired):
        rot.end()
        print("\nRotator was interrupted")
    except Exception:
        rot.end()
        print("\nSome problem occured")
