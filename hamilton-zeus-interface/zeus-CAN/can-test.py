import can
import time

can.rc['interface'] = 'kvaser'
can.rc['channel'] = '0'
can.rc['bitrate'] = 500000
from can.interface import Bus

bus = Bus()

msg = can.Message(
    arbitration_id=0xC0FFEE, data=[0, 25, 0, 1, 3, 1, 4, 1], is_extended_id=True)

for i in range(100):
    bus.send(msg)
    print(f"message sent on {bus.channel_info}")
    time.sleep(1)

print(bus.channel_info)

print(bus.state)