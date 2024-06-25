import socket
import subprocess
import time

import yaml

from lib.configuration import rot_configutarion as conf

with open("lib/configuration/rot_config.yaml", "r") as file:
    config = yaml.safe_load(file)


class Rotator:
    def __init__(
        self,
        rotconfig=config,
        verbose=False,
    ):
        rotname = rotconfig["select"]
        config = rotconfig[rotname]
        attributes = ["daemoncmd", "host", "port", "model", "device", "sspeed"]
        for attr in attributes:
            setattr(self, attr, config[attr] if attr in config else None)
        self.verbose = verbose

        print(self.cmd_options())

        self.start_daemon()
        # TODO: replace sleep for a non blocking wait
        time.sleep(3)
        if self.host and self.port:
            self.open_socket()

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

            if prompt in ["getpos", "g"]:
                az, el = rot.get_pos()
                print(f"AZ: {az}; EL: {el}")
            elif prompt in ["setpos", "s"]:
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
