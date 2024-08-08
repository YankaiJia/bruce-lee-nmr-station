from flask import Flask, render_template, request

from xml_converter import load_protocols, to_xml_request
# from spectrometer import send_request_to_spinsolve80

app = Flask(__name__)

process_order = []

valid_protocol = {}
available_protocols = ["1D PROTON", "1D EXTENDED+", "1D WET SUP"]
current_protocol = ""

xml_request_message = ""
protocol_perform_list = []

@app.route('/')
def index():
    return render_template('index.html.j2', protocols=available_protocols)

@app.route('/save-process-order', methods=['POST'])
def save_process_order():
    submission = request.form.get('process-order', '')

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
    return  render_template('protocol_param.html.j2', params=valid_protocol[current_protocol], current_mode=current_mode)

@app.route('/select_protocol_mode')
def select_protocol_mode():
    current_protocol_mode = request.args.get("Mode")
    return render_template('protocol_mode_param.html.j2', current_protocol_mode=current_protocol_mode)

@app.route('/add_protocol', methods=['POST', 'GET'])
def add_protocol():
    submission = request.form
    
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
    xml_request_message = [to_xml_request("Save", obj) for obj in protocol_perform_list]

    # start automation 
    # create scheduler

if __name__ == '__main__' :
    app.debug = True
    valid_protocol = load_protocols()
    valid_protocol['Select Protocol'] = {}
    available_protocols = valid_protocol.keys()

    app.run()
