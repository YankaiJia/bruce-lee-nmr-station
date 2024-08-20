import sys 
sys.path.append("..") 
from xml_converter import to_xml_request
from spectrometer import SpectrometerRemoteControl

def test_get_user_record():
  remote_control = SpectrometerRemoteControl()

  user_record_field_name = ["Solvent", "Sample", "Custom", "DataFolder", "UserData"]
  for field_name in user_record_field_name:
    message = to_xml_request("GetRequest", field_name)
    remote_control.send_request_to_spinsolve80(message, 3)

    """
    no response for DataFolder
    UserData need special handle in to_xml_request
      - not sure the usage of this
    """

def test_quick_shim_reference():
  remote_control = SpectrometerRemoteControl()
  message = """<?xml version="1.0" encoding="utf-8"?>\n<Message>\n\t<Start protocol="1D PROTON">\n\t\t<Option name="Scan" value="StandardScan" />\n\t</Start>\n</Message>"""
  remote_control.send_request_to_spinsolve80(message, 3)

if __name__ == "__main__":
  # test_get_user_record()
  test_quick_shim_reference()