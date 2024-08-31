from flask import Flask, render_template, request

import datetime

from scheduler import Scheduler, PipetterDecision, RobotArmDecision, NMR_SpectrometerDecision

from robotic_arm import RobotArm
from pipetter import PipetterControl
from spectrometer import SpectrometerRemoteControl, load_protocols, to_xml_request

# these three are for testing
# from tests.dummy_robotarm import DummyRobotArmControl as RobotArm
# from tests.dummy_pipetter import DummyPipetterControl as PipetterControl
# from tests.dummy_spectrometer import DummySpectrometerRemoteControl as SpectrometerRemoteControl

from spectrometer import load_protocols, to_xml_request


app = Flask(__name__)
remote_control = SpectrometerRemoteControl()

process_order = []

valid_protocol = {}
available_protocols = ["1D PROTON", "1D EXTENDED+", "1D WET SUP"]
current_protocol = ""

xml_request_messages = []
protocol_perform_list = []

# This one must be written in Windows Format file path
next_automation_dir = ""

@app.route('/')
def index():
    return render_template('index.html.j2', protocols=available_protocols)


@app.route('/save-user-record', methods=['POST'])
def save_user_record():
    user_record = request.form
    print(f"user-record submitted: {user_record}")

    for field_name in user_record:
        message = to_xml_request("Set", {field_name: user_record[field_name]})
        print(message)  
        remote_control.send_request_to_spinsolve80(message)

    return "Saved!"


@app.route('/save-plate-id', methods=['POST'])
def save_plate_id():
    vial_plate_id = request.form
    print(f"vial plate id is {vial_plate_id}")

    global next_automation_dir
    
    # TODO: add the desired dropbox drive spectrum storage folder path in the settings and put back to here, must be Windows format
    spectrum_storage_path = ""
    today_ymd = datetime.now().strftime('%Y%m%d')
        
    next_automation_dir = spectrum_storage_path + "\\" + today_ymd + "\\" + str(vial_plate_id) + "\\"
    # and then in each automation a subfolder insode next_automation_dir will be created based on the sampleId of the vial
    # not sure what happen for each protocol in each sample, wil it create its own folder
    # go update (in spectrometer/spectrometer.py) the NMR_Spectrometer.send_request_to_spinsolve80 update the folder path before new sample analysis

    return f"next_automation_dir is now: {next_automation_dir}"

@app.route('/save-process-order', methods=['POST'])
def save_process_order():
    submission = request.form.get('process-order', '')

    global process_order 
    process_order = [int(id.strip()) for id in submission.split(',') if id.strip()]

    print(process_order)

    return "Saved!"


@app.route('/get_protocol_selection')
def get_protocol_selection():
    return render_template('protocol_selection.html.j2', protocols=available_protocols)

@app.route('/get_protocol_param')
def get_protocol_param():
    global current_protocol
    next_protocol = request.args.get("protocol")
    if next_protocol: 
        current_protocol = next_protocol
    current_mode = request.args.get("Mode", "Auto")

    print(f"You just selected the protocol {current_protocol}")
    return  render_template(
        'protocol_param.html.j2', 
        params=valid_protocol[current_protocol], 
        current_protocol_mode=current_mode
    )

@app.route('/select_protocol_mode')
def select_protocol_mode():
    current_protocol_mode = request.args.get("Mode")

    return render_template(
        'protocol_mode_param.html.j2', 
        params=valid_protocol[current_protocol], 
        current_protocol_mode=current_protocol_mode
    )

@app.route('/add_protocol', methods=['POST', 'GET'])
def add_protocol():
    submission = request.form

    print(to_xml_request("Start", submission))

    global protocol_perform_list
    protocol_perform_list.append(submission)
  
    return render_template('protocol_perform_list.html.j2', protocols=protocol_perform_list)

    
@app.route('/get_protocol_perform_list')
def get_protocol_perform_list():
    return 

@app.route('/protocol-item/<int:item_id>', methods=['Delete'])
def delete_protocol_item(item_id: int):
    protocol_perform_list.pop(item_id - 1)
    return render_template('protocol_perform_list.html.j2', protocols=protocol_perform_list)


@app.route('/start_automation')
def start_automation():
    xml_request_messages = [to_xml_request("Start", obj) for obj in protocol_perform_list]
    print(xml_request_messages)
    # start automation 

    global scheduler
    global process_order
    
    pipetter = PipetterDecision(PipetterControl(), process_order)
    robot_arm = RobotArmDecision(RobotArm())
    spectrometer = NMR_SpectrometerDecision(SpectrometerRemoteControl(), next_automation_dir, xml_request_messages)
    scheduler = Scheduler(pipetter, robot_arm, spectrometer)


    scheduler.start()

    scheduler = None

    return "Scheduler started!"


if __name__ == '__main__' :
    app.debug = True
    valid_protocol = load_protocols()
    valid_protocol['Select Protocol'] = {}
    available_protocols = valid_protocol.keys()

    app.run()
