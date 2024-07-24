import xml.etree.ElementTree as ET
# for protocol in protocols:
#     protocol_name = protocol.get('protocol')
#     if not protocol_name in ['1D PROTON', '1D EXTENDED+', '1D WET SUP']:
#         continue
#     print(protocol_name)
#     options = protocol.findall('Option')
#     for option in options:
#         option_name = option.get('name')
#         print(f"\-->{option_name}")
#         for value in option:
#             print(f"    \-->{value.text}")

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

if __name__ == "__main__":
    load_protocols()