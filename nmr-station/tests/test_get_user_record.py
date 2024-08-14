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

if __name__ == "__main__":
  test_get_user_record()