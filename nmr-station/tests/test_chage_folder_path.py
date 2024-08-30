from datetime import datetime

from spectrometer import to_xml_request, SpectrometerRemoteControl

def test():
  remote_control = SpectrometerRemoteControl()
  spectrum_storage_path = "SPECTRUM_STORAGE_PATH"
  today_ymd = datetime.now().strftime('%Y%m%d')
  spectrum_storage_dir = spectrum_storage_path + "\\" + today_ymd + "\\" 

  for i in range(5):
    cur_path = spectrum_storage_dir + "\\" + str(i)
    set_folder_xml_msg = to_xml_request("SetFolderName", cur_path)
    remote_control.send_request_to_spinsolve80(set_folder_xml_msg)
    
    test_xml_msg = """<?xml version="1.0" encoding="utf-8"?>
<Message>
        <Start protocol="1D PROTON">
                <Option name="Scan" value="QuickScan" />
        </Start>
</Message>"""
    remote_control.send_request_to_spinsolve80(test_xml_msg)
    remote_control.send_request_to_spinsolve80(test_xml_msg)

if __name__ == "__main__":
  test()