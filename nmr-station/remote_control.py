import sys, os, socket, time

def send_request_to_spinsolve80(request_content: str):
  HOST = "127.0.0.1"
  PORT = 13000

  print(f"Connect to {HOST}:{PORT}")
  spinsolve_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  spinsolve_socket.connect((HOST, PORT))

  print(request_content)

  spinsolve_socket.send(request_content.encode())
  spinsolve_socket.settimeout(20)
  try: 
    while True:
      time.sleep(0.2)
      chunk = spinsolve_socket.recv(8192)
      if chunk:
        print(chunk.decode())
    
  except socket.error as msg:
    spinsolve_socket.settimeout(None)

  print('\r\nClose Connection')
  spinsolve_socket.close()


if __name__ =="__main__":
    available_protocol_options_request = """<?xml version="1.0" encoding="utf-8"?>
    <Message>
      <AvailableProtocolOptionsRequest/>
    </Message>
    """

    get_request_content = """<?xml version="1.0" encoding="utf-8"?>
    <Message>
        <GetRequest>
            <Sample />
        </GetRequest>
    </Message>
    """

    testing_shim_content = """
    <?xml version="1.0" encoding="utf-8"?>
    <Message>
        <Start protocol="SHIM">
            <Option name="Shim" value="QuickShim" />
        </Start>
    </Message>
    """
    # send_request_to_spinsolve80(testing_shim_content)
