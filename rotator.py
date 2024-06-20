import socket
import subprocess
import time

host = "localhost"
port = 4533
model = "1"


class Rotator:
    def __init__(self, host, port, model):
        self.host = host
        self.port = port
        self.model = model
        self.start_daemon()
        time.sleep(1)
        self.open_socket()

    def start_daemon(self):
        self.daemon = subprocess.Popen(
            [
                "rotctld",
                "-m",
                self.model,
                "-T",
                self.host,
                "-t",
                str(self.port),
                "-vvvvvvvv",
            ]
        )

    def terminate_daemon(self):
        self.daemon.terminate()
        self.daemon.wait()

    def open_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def close_socket(self):
        self.socket.close()

    def get_pos(self):
        cmd = "p"
        buffsize = 20
        self.socket.send(cmd.encode())
        return self.socket.recv(buffsize).decode().split()

    def set_pos(self, az, el):
        cmd = f"P {az} {el}\x0a"
        buffsize = 20
        self.socket.send(cmd.encode())
        return self.socket.recv(buffsize).decode()

    def end(self):
        self.close_socket()
        self.terminate_daemon()
        print("\nRotator Terminated")


if __name__ == "__main__":
    rot = Rotator(host, port, model)

    try:
        while True:
            prompt = input(">>> ")

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
