# LIQUID CLASS



`
`

`
``
















# example of a liquid class para
# GMid0001 lq01 uu0 0 05000 0050 00050 00250 0200 010 0 3 3 0 0 05000 00000 000 00050 040 0200 010 00325

import zeus
import time
import json


zm = zeus.ZeusModule(id=1)

liquid_class_table_para = {}

def get_liquid_class_parameter(id = '0001', liquid_index = '00'):
    cmd = 'GMid'+ id + 'lq' + liquid_index
    print(f'cmd send is : {cmd}')
    zm.sendCommand(cmd) # Here i send cmd twice because the msg buffer save the prvious data. this is dumb, but it works
    # print(zm.r.received_msg)
    time.sleep(1)
    zm.sendCommand(cmd)
    msg_received_from_Zeus = zm.r.received_msg
    print(f'msg_received_from_Zeus len is : {len(msg_received_from_Zeus)}')
    return msg_received_fro`
    m_Zeus


def fill_one_liquid_class_parameter(id = '0001', liquid_index = '00'):
    msg = get_liquid_class_parameter(id, liquid_index)
    para_container = ''.join(i for i in msg if i.isdigit())
    # print(para_container)
    global liquid_class_table_para
    var_dict = {'id': 4,
                 'index': 2,
                 'liquidClassForFilterTips': 1,
                 'aspirationMode': 1,
                 'aspirationFlowRate': 5,
                 'overAspiratedVolume': 4,
                 'aspirationTransportVolume': 5,
                 'blowoutAirVolume': 5,
                 'aspirationSwapSpeed': 4,
                 'aspirationSettlingTime': 3,
                 'lld': 1,
                 'clldSensitivity': 1,
                 'plldSensitivity': 1,
                 'adc': 1,
                 'dispensingMode': 1,
                 'dispensingFlowRate': 5,
                 'stopFlowRate': 5,
                 'stopBackVolume': 3,
                 'dispensingTransportVolume': 5,
                 'acceleration': 3,
                 'dispensingSwapSpeed': 4,
                 'dispensingSettlingTime': 3,
                 'flowRateTransportVolume': 5} # store variables and its len
    if not sum(var_dict.values()) ==  len (para_container):
        print("Msg string length does not match the needed length!")
        return
    n = 0
    for i in var_dict:
        # print(f'liquid index is : {liquid_index}')
        liquid_class_table_para[liquid_index][i] = int(para_container[n:n+var_dict[i]])
        n += var_dict[i]
    return liquid_class_table_para

def extract_all_built_in_liquid_class_parameters_to_a_dict():
    global liquid_class_table_para
    liquid_class_table_para = {}
    for i in range(18):
        liquid_index = str(i).zfill(2)
        # print(liquid_index)
        liquid_class_table_para[liquid_index] = {}
        fill_one_liquid_class_parameter(liquid_index = liquid_index)
        # print(liquid_class_table_para)
        time.sleep(1)
    # print(liquid_class_table_para)
    with open('liquid_class_table_para_ALL.json', 'w', encoding='utf-8') as f:
        json.dump(liquid_class_table_para, f, ensure_ascii=False, indent=4)
    print(f'data save: {liquid_class_table_para}')


# extract_all_built_in_liquid_class_parameters_to_a_dict()

# load jason file
with open('liquid_class_table_para_ALL.json') as json_file:
    liquid_class_table_para = json.load(json_file)

# liquid_class_table_para['18'] = liquid_class_table_para['14']
# liquid_class_table_para['18']['index'] = 18
# liquid_class_table_para['18']['plldSensitivity'] = 2

liquid_class_table_para['19'] = liquid_class_table_para['02']
liquid_class_table_para['19']['index'] = 19
liquid_class_table_para['19']['lld'] = 1
# liquid_class_table_para['19']['plldSensitivity'] = 2

# update json file
with open('liquid_class_table_para_ALL.json', 'w', encoding='utf-8') as f:
    json.dump(liquid_class_table_para, f, ensure_ascii=False, indent=4)

# pp(db['han'])