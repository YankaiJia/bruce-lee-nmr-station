"""
This scirpt is for liquid class storing and setting.

Working steps:
    1 extract all the parameters for the built-in liquid classes.
    2 store all the extracted parameters to a dictionary. step 1 and 2 need to be done only once.
        ## extract_all_built_in_liquid_class_parameters_to_a_dict()
    3 name your new liquid class from index 21, because the first 20 index are read only. Copy one of the liquid class
      parameters to your new liquid class.
        ## copy_para_from_to(index_from, index_to)
    4 modify your new liquid class by setting new parameters
        ## liquid_class_table_para['21']['lld'] = 1
        ## liquid_class_table_para['21']['plldSensitivity'] = 3
    5 update your local dictionary, i.e., Json file.
        ## update_liquid_dict()
    6 set your new liquid class to zeus
        ## set_liquid_class_to_zeus( liquid_index)
    7 check your liquid class parameters from zeus
        ## request_parameters_from_zeus(liquid_index):

Notes
    1 do not forget the space between parameters when sending it the zeus
    2 there is one glitch with 'GG' and 'GH' commands. See inside function: set_liquid_class_to_zeus( liquid_index)

Yankai Jia 2023/01/23
"""


import zeus
import time
import json
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# ## this is for the first time usage.
# liquid_class_table_para = {
#     'data_container': {},
#     'liquid_class_para':{},
#     'calibration':{ 'aspiration': {}, 'dispensing':{}},
#     'qpm':{'aspiration': {}, 'dispensing':{}}
# }

# load jason file
def open_json():
    with open('data/liquid_class_table_para_ALL.json') as json_file:
        liquid_class_table_para = json.load(json_file)
    return liquid_class_table_para

liquid_class_table_para = open_json()

def extract_liquid_class_parameter(liquid_index:int, id:str = '0001'):
    cmd = 'GMid'+ id+ 'lq' + str(liquid_index).zfill(2)
    print(f'cmd send is : {cmd}')
    zm.sendCommand(cmd) # Here i send cmd twice because the msg buffer save the prvious data. this is dumb, but it works
    # print(zm.r.received_msg)
    temp = zm.r.received_msg
    print(temp)
    time.sleep(1)
    zm.sendCommand(cmd)
    msg_received_from_Zeus = zm.r.received_msg
    print(f'msg_received_from_Zeus len is : {len(msg_received_from_Zeus)}')
    return msg_received_from_Zeus

def extract_calibration_aspiration(liquid_index, id = '0001'):

    cmd = 'GEid'+ id+ 'gg' + str(liquid_index).zfill(2)
    print(f'cmd send is : {cmd}')
    zm.sendCommand(cmd)  # Here i send cmd twice because the msg buffer save the prvious data. this is dumb, but it works
    # print(zm.r.received_msg)
    temp = zm.r.received_msg
    print(temp)
    time.sleep(1)
    zm.sendCommand(cmd)
    msg_received_from_Zeus = zm.r.received_msg
    print(f'msg_received_from_Zeus for calibration_aspiration is : {msg_received_from_Zeus}')
    return msg_received_from_Zeus


def extract_calibration_dispensing(liquid_index, id = '0001'):
    cmd = 'GIid' + id + 'gh' + str(liquid_index).zfill(2)
    print(f'cmd send is : {cmd}')
    zm.sendCommand(
        cmd)  # Here i send cmd twice because the msg buffer save the prvious data. this is dumb, but it works
    # print(zm.r.received_msg)
    temp = zm.r.received_msg
    print(temp)
    time.sleep(1)
    zm.sendCommand(cmd)
    msg_received_from_Zeus = zm.r.received_msg
    print(f'msg_received_from_Zeus for calibration_dispensing is : {msg_received_from_Zeus}')
    return msg_received_from_Zeus


def extract_qpm_aspiration(liquid_index, id = '0001'):
    cmd = 'GSid' + id + 'gv' + str(liquid_index).zfill(2)
    print(f'cmd send is : {cmd}')
    zm.sendCommand(cmd)  # Here i send cmd twice because the msg buffer save the prvious data. this is dumb, but it works
    # print(zm.r.received_msg)
    temp = zm.r.received_msg
    print(temp)
    time.sleep(1)
    zm.sendCommand(cmd)
    msg_received_from_Zeus = zm.r.received_msg
    print(f'msg_received_from_Zeus for qpm_aspiration is : {msg_received_from_Zeus}')
    return msg_received_from_Zeus


def extract_qpm_dispensing(liquid_index, id = '0001'):
    cmd = 'GWid' + id + 'gp' + str(liquid_index).zfill(2)
    print(f'cmd send is : {cmd}')
    zm.sendCommand(cmd)  # Here i send cmd twice because the msg buffer save the prvious data. this is dumb, but it works
    # print(zm.r.received_msg)
    temp = zm.r.received_msg
    print(temp)
    time.sleep(1)
    zm.sendCommand(cmd)
    msg_received_from_Zeus = zm.r.received_msg
    print(f'msg_received_from_Zeus for qpm_dispensing is : {msg_received_from_Zeus}')
    return msg_received_from_Zeus


def fill_one_liquid_class_parameter( liquid_index, id = '0001'):
    msg = extract_liquid_class_parameter(id = id, liquid_index = liquid_index)
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
    # if not sum(var_dict.values()) +  ==  len (para_container):
    #     print("Msg string length does not match the needed length!")
    #     return
    n = 0
    for i in var_dict:
        # print(f'liquid index is : {liquid_index}')
        liquid_class_table_para['liquid_class_para'][liquid_index][i] = int(para_container[n:n+var_dict[i]])
        n += var_dict[i]
    return liquid_class_table_para


def extract_all_built_in_liquid_class_parameters_to_a_dict():
    global liquid_class_table_para
    for i in range(31):
        liquid_index = str(i).zfill(2)

        liquid_class_table_para['liquid_class_para'][liquid_index] = {}
        fill_one_liquid_class_parameter(liquid_index, id = '0001')

        liquid_class_table_para['calibration']['aspiration'][liquid_index] = {}
        string1 = extract_calibration_aspiration(liquid_index, id='0001')
        liquid_class_table_para['calibration']['aspiration'][liquid_index] = string1[:-3]

        liquid_class_table_para['calibration']['dispensing'][liquid_index] = {}
        string2 = extract_calibration_dispensing(liquid_index, id='0001')
        liquid_class_table_para['calibration']['dispensing'][liquid_index] = string2[:-3]

        liquid_class_table_para['qpm']['aspiration'][liquid_index] = {}
        string3 = extract_qpm_aspiration(liquid_index, id='0001')
        liquid_class_table_para['qpm']['aspiration'][liquid_index] = string3[:-4]

        liquid_class_table_para['qpm']['dispensing'][liquid_index] = {}
        string4 = extract_qpm_dispensing(liquid_index, id='0001')
        liquid_class_table_para['qpm']['dispensing'][liquid_index] = string4

# extract_all_built_in_liquid_class_parameters_to_a_dict() # Do this only when needed

def copy_para_from_to(index_from, index_to):
    liquid_class_table_para['liquid_class_para'][str(index_to).zfill(2)] = liquid_class_table_para['liquid_class_para'][str(index_from).zfill(2)]
    liquid_class_table_para['liquid_class_para'][str(index_to).zfill(2)]['index'] = index_to  # Update new liquid index

    string1 = liquid_class_table_para['calibration']['aspiration'][str(index_from).zfill(2)]
    new_string1 = 'GGid0001gg' + str(index_to).zfill(2) + string1[12:] # Update new liquid index and change GE (reequest) to GG (set)
    liquid_class_table_para['calibration']['aspiration'][str(index_to).zfill(2)] = new_string1

    string2 = liquid_class_table_para['calibration']['dispensing'][str(index_from).zfill(2)]
    new_string2 = 'GHid0001gh' + str(index_to).zfill(2) + string2[12:] # Update new liquid index and change GI(reequest) to GH (set)
    liquid_class_table_para['calibration']['dispensing'][str(index_to).zfill(2)] = new_string2

    string3 = liquid_class_table_para['qpm']['aspiration'][str(index_from).zfill(2)]
    new_string3 = 'GQid0001gv' + str(index_to).zfill(2) + string3[12:] # Update new liquid index and change GS (reequest) to GQ (set)
    liquid_class_table_para['qpm']['aspiration'][str(index_to).zfill(2)] = new_string3

    string4 = liquid_class_table_para['qpm']['dispensing'][str(index_from).zfill(2)]
    new_string4 = 'GVid0001gp' + str(index_to).zfill(2) + string4[12:] # Update new liquid index and change GW (reequest) to Gv (set)
    liquid_class_table_para['qpm']['dispensing'][str(index_to).zfill(2)] = new_string4

    update_liquid_dict()

# copy_para_from_to(index_from = 1, index_to = 30)
## modify your new liquid class parameters
# liquid_class_table_para['data_container']['21'] = 'DMF, based on water 02, tip 1000ul'
# liquid_class_table_para['data_container']['22'] = 'DMF, based on water 01, tip 300ul'
# liquid_class_table_para['data_container']['23'] = 'DMF, based on water 00, tip 50ul'

# liquid_class_table_para['21']['lld'] = 1
# # liquid_class_table_para['21']['plldSensitivity'] = 3


def update_liquid_dict():
    # update json file
    with open('data/liquid_class_table_para_ALL.json', 'w', encoding='utf-8') as f:
        json.dump(liquid_class_table_para, f, ensure_ascii=False, indent=4)

# update_liquid_dict()

def set_liquid_class_to_zeus( liquid_index):
    # write liquid class parameters
    para1 = liquid_class_table_para['liquid_class_para'][str(liquid_index).zfill(2)]
    lc_param = zeus.LiquidClass(**para1)
    zm.setLiquidClassParameters(lc_param)
    time.sleep(0.5)

    ## write calibration curve
    # aspiration
    para2 = liquid_class_table_para['calibration']['aspiration'][str(liquid_index).zfill(2)]
            ## There is a firmware malfuction here. Instead of send the string: GGid0001gg21ck + parameters. You should remove
            ## gg21 from the string and send this:GGid0001ck + parameters. But before send this, you should do this:
            ## zm.sendCommand('GHid0001gh21') and zm.sendCommand('RAid0000ragh'). Yaroslav figured this out. There was a lot of frustration
            ## before this was figured out.
    zm.sendCommand('GGid0001gg'+str(liquid_index).zfill(2))
    time.sleep(0.5)
    zm.sendCommand('RAid0000ragg')
    time.sleep(0.5)
    para2_new = para2[:8] + para2[12:]
    zm.sendCommand(para2_new)
    time.sleep(0.5)
    # dispensing
    para3 = liquid_class_table_para['calibration']['dispensing'][str(liquid_index).zfill(2)]
    zm.sendCommand('GHid0001gh'+str(liquid_index).zfill(2))
    time.sleep(0.5)
    zm.sendCommand('RAid0000ragh')
    time.sleep(0.5)
    para3_new = para3[:8] + para3[12:]
    zm.sendCommand(para3_new)
    time.sleep(0.5)
    #
    # set_liquid_class_to_zeus(liquid_index = 21)
    # set_liquid_class_to_zeus(liquid_index = 22)
    ## write qpm
    # aspiration
    para4 = liquid_class_table_para['qpm']['aspiration'][str(liquid_index).zfill(2)]
    zm.sendCommand(para4)
    time.sleep(0.5)
    # dispensing
    para5 = liquid_class_table_para['qpm']['dispensing'][str(liquid_index).zfill(2)]
    zm.sendCommand(para5)
    time.sleep(0.5)

def request_parameters_from_zeus(liquid_index):

    # liquid parameters
    zm.sendCommand('GMid0001lq' + str(liquid_index).zfill(2))
    time.sleep(0.5)

    # calibrations
    zm.sendCommand('GEid0001gg' + str(liquid_index).zfill(2))
    time.sleep(0.5)
    zm.sendCommand('GIid0001gh' + str(liquid_index).zfill(2))
    time.sleep(0.5)

    # qpm
    zm.sendCommand('GSid0001gv' + str(liquid_index).zfill(2))
    time.sleep(0.5)
    zm.sendCommand('GWid0001gp' + str(liquid_index).zfill(2))
    time.sleep(0.5)

# set_liquid_class_to_zeus( liquid_index =23 )
# time.sleep(1)
# request_parameters_from_zeus(liquid_index = 23)

# request_parameters_from_zeus(liquid_index = 22)

## the following code is for easy of typing in python console. Use with care.
def wr(liquid_index):
    set_liquid_class_to_zeus(liquid_index = liquid_index )
def re(liquid_index):
    request_parameters_from_zeus(liquid_index = liquid_index)

def set():
    copy_para_from_to(index_from = 2, index_to = 21)
    copy_para_from_to(index_from = 1, index_to = 22)
    copy_para_from_to(index_from = 0, index_to = 23)
    for i in range(21,24):
        wr(str(i))
        re(str(i))
    print('Finished!')

def get(liquid_index):
    return extract_liquid_class_parameter(liquid_index= liquid_index)

# set()

 # example of a liquid class para
# GMid0001 lq01 uu0 0 05000 0050 00050 00250 0200 010 0 3 3 0 0 05000 00000 000 00050 040 0200 010 00325


## copy liquid class parameters from one index to another index
## this is a dumb way to do it. Just copy in the dictionary and then load from the dictionary.
# def copy_para_from_to(index_from, index_to):
#     received_string = extract_liquid_class_parameter(id='0001', liquid_index=str(index_from).zfill(2))
#     print(f'The index_from class is:  {received_string}')
#     assembly_string = 'GMid0001lq' + str(index_to).zfill(2) + received_string[12:100]
#     zm.sendCommand(assembly_string)
#     new_class_para = extract_liquid_class_parameter(id='0001', liquid_index=str(index_to).zfill(2))
#     print(f'The new class para is:  {new_class_para}')

###############################################################
######################### For QPM #############################

def open_qpm():
    with open('calibration_for_pipetting/qpm_asp_water_300ul_asp_index01.json') as json_file:
        qpm = json.load(json_file)
    return qpm

# qpm = open_qpm()

def plot_pressure_curve(aa):
    # data = get_pressure_curve()
    color_dict = mcolors.TABLEAU_COLORS
    color = [key for key in color_dict.keys() ]
    i = 0
    for key, value in aa.items():
        xx= list(range(len(value)))
        plt.plot(xx, value, '.', color=color[i%10], label='No mask')
        i += 1

    return plt

# plot_pressure_curve(qpm)
# plt.show()


# a = [902,868,902,900,902,902,898,898]
# b = [895,828,893,871,885,845,816,786]
# c = []
# for i in range(len(a)):
#     c.append((a[i]-b[i])/2)


if __name__ == "__main__":
    zm = zeus.ZeusModule(id=1)
