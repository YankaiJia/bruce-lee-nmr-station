import xml.etree.ElementTree as ET

def load_protocols() -> dict:
    tree = ET.parse("templates/ProtocolOptions.xml")
    protocols = tree.find('ProtocolOptions')

    valid_protocol = {}
    for protocol in protocols:
        protocol_name = protocol.get('protocol')
        params = protocol.findall('Option')
        if params == []: continue 
        valid_protocol[protocol_name] = {} 
        for param in params:
            param_name = param.get("name")
            options = param.findall("Value")
            if options[0].text == None:
                valid_protocol[protocol_name][param_name] = {
                    "type": "input"
                }
            else:
                valid_protocol[protocol_name][param_name] = {
                    "type": "select",
                    "options": [option.text for option in options]
                }

    return valid_protocol

def to_xml_request(message_type: str, content):
    message_head = """<?xml version="1.0" encoding="utf-8"?>
<Message>
"""
    message_body = ""
    
    if message_type == "Start":
        message_body = f"\t<Start protocol=\"{content['protocol']}\">\n"
        for key in content:
            if key != "protocol":
                option_name, option_value = key, content[key]
                message_body += f"\t\t<Option name=\"{option_name}\" value=\"{option_value}\" />\n"
        message_body += "\t</Start>\n"
    
    elif message_type == "Set":
        message_body = "\t<Set>\n"
        for key in content:
            message_body += f"\t\t<{key}> {content[key]} </{key}>\n"
        message_body += "\t</Set>\n"

    elif message_type == "GetRequest":
        message_body = f"\t<GetRequest>\n\t\t<{content}/>\n\t</GetRequest>\n"

    elif message_type == "SetFolderName":
        message_body = "\t<Set>\n\t\t<DataFolder>\n\t\t\t<TimeStampTree>"
        message_body += f"{content}"
        message_body += "</TimeStampTree>\n\t\t</DataFolder>\n\t</Set>\n"
    
    message_tail = "</Message>"
    request_message = message_head + message_body + message_tail
    
    return request_message

if __name__ == "__main__":
    load_protocols()