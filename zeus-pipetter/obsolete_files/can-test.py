import can
import time

can.rc['interface'] = 'kvaser'
can.rc['channel'] = '0'
can.rc['bitrate'] = 500000
from can.interface import Bus

bus = Bus()

# data=[0, 25, 0, 1, 3, 1, 4, 1]

list = [52, 46, 69, 64, 31, 31, 39, 71] #data in hex
data = [] # data in dec

for i in list:
    i = str(i)
    data.append(int(i, base = 16))
print(data)


msg = can.Message(
    arbitration_id=5, data=data, is_extended_id=True)

for i in range(10):
    bus.send(msg)
    print(f"message sent on {bus.channel_info}")
    # print(f"Msg sent. Id: {msg.arbitration_id}. data: {data[0].decode()} ")
    time.sleep(1)


print(bus.channel_info)

print(bus.state)

