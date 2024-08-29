import sys, os, socket, time

sys.path.append(os.path.abspath(os.path.pardir))

from settings import REMOTE_CONTROL_PORT, REMOTE_CONTROL_HOST, REMOTE_CONTROL_TIMEOUT



class DummySpectrometerRemoteControl:
    def __init__(self) -> None:
        print("RemoteControl initiated")

    def send_request_to_spinsolve80(self, request_content: str):
        print("sent request to spinsolve80 with the following message")
        print(request_content)
        print()

class SpectrometerRemoteControl:
    def __init__(self) -> None:
        self.spinsolve_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.HOST = REMOTE_CONTROL_HOST  # type is string
        self.PORT = REMOTE_CONTROL_PORT  # type is string, convert to int when sending to socket.connect()

    def send_request_to_spinsolve80(self, request_content: str, timeout_second:float = REMOTE_CONTROL_TIMEOUT):
        print(f"Connect to {self.HOST}:{self.PORT}")
        # print(f"type of self.HOST and self.PORT: {type(self.HOST)},{type(self.PORT)}")
        self.spinsolve_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.spinsolve_socket.connect((self.HOST, int(self.PORT)))

        print(request_content)

        self.spinsolve_socket.send(request_content.encode())
        self.spinsolve_socket.settimeout(timeout_second)
        try:
            while True:
                time.sleep(0.2)
                chunk = self.spinsolve_socket.recv(8192)
                if chunk:
                    print(chunk.decode())

        except socket.error as msg:
            self.spinsolve_socket.settimeout(None)

        print("\r\nClose Connection")
        self.spinsolve_socket.close()
    

if __name__ == "__main__":
    # pass
    # send_request_to_spinsolve80(testing_shim_content)


    sp = SpectrometerRemoteControl()