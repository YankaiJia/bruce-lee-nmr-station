import flask

from xml_converter import load_protocols

app = flask.Flask(__name__)

valid_protocol = {}
available_protocols = ["1D PROTON", "1D EXTENDED+", "1D WET SUP"]
current_protocol = ""

@app.route('/')
def index():
    return flask.render_template('index.html', protocols=available_protocols)

@app.route('/select_protocol/')
def select_protocol():
    global current_protocol
    next_protocol = flask.request.args.get("protocol")
    if next_protocol: 
        current_protocol = next_protocol
    current_mode = flask.request.args.get("freq_search_mode", "Auto")

    print(f"You just selected the protocol {current_protocol}")
    return flask.render_template('protocol_params_with_mode.html', params=valid_protocol[current_protocol], current_mode=current_mode)


if __name__ == '__main__' :
    app.debug = True
    valid_protocol = load_protocols()
    valid_protocol['Select Protocol'] = {}
    # available_protocols = valid_protocol.keys()

    print(available_protocols)

    app.run()
