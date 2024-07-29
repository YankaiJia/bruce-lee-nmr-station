class DummySpectrometerRemoteControl:
    def __init__(self) -> None:
        print("RemoteControl initiated")

    def send_request_to_spinsolve80(self, request_content: str):
        print("sent request to spinsolve80 with the following message")
        print(request_content)
        print()