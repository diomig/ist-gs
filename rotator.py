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

    def get_pos_rot(self):
        cmd = "p"
        buffsize = 20
        self.socket.send(cmd.encode())
        return self.socket.recv(buffsize).decode().split()

    def end(self):
        self.close_socket()
        self.terminate_daemon()



if __name__ == "__main__":
    rot = Rotator(host, port, model)

    # Start the daemon
    # daemon = start_daemon(rot)

    #   rot.open_socket()
    try:
        while True:

            az, el = rot.get_pos_rot()
            print(f"AZ: {az}; EL: {el}")
            time.sleep(1)

    except (KeyboardInterrupt, subprocess.TimeoutExpired):
        rot.end()
        print('\nRotator Terminated')
