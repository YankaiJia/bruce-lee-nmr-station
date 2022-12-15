import can
import logging
import signal
import time
from time import sleep
from colorama import init, Fore, Back, Style
from threading import Thread, Lock
import codecs
import sys

DEBUG = 0
INFO = 0
WARNING = 1
ERROR = 1
# KICK_MASK = 0x0400
KICK_MASK = 0b10000000000
SENDER_ID_MASK = 0x03E0
RECEIVER_ID_MASK = 0x001F
EOM_MASK = 0b10000000

# # NOTE TO SELF:
# # this is how the respective can.Message code was modified for all this to work:
# #
# if data is None or is_remote_frame:
#     self.data = bytearray()
# elif isinstance(data, bytearray) or isinstance(data, bytes):
#     self.data = data
#     if isinstance(data, bytearray):
#         print('data is bytearray')
#     if isinstance(data, bytes):
#         print('data is bytes')
#     print(f'len of data = {len(self.data)}')
#     print(f'data is {data}')
# else:
#     try:
#         if type(data) == type(0):
#             print('data is int')
#             self.data = bytearray(data)
#             print(self.data)
#             print(f'len of data = {len(self.data)}')
#         else:
#             print('data is string')
#             self.data = bytearray(data, encoding='iso-8859-1')
#             print(self.data)
#             print(f'len of data = {len(self.data)}')
#     except TypeError as error:
#         err = f"Couldn't create message from {data} ({type(data)})"
#         print(err)
#         print(data)
#         # raise TypeError(err) from error
#         raise TypeError(error)


class Unbuffered(object):

    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


# sys.stdout = Unbuffered(sys.stdout)


def printMSG(type, msg):
    ts = time.time()  # Timestamp
    if (type == 'info' and INFO == 1):
        print(
            Fore.WHITE + "(" + "{0:f}".format(ts) + ") INFO: " + msg + Style.RESET_ALL)

    elif (type == 'debug' and DEBUG == 1):
        print(Fore.MAGENTA +
              "(" + "{0:f}".format(ts) + ") DEBUG: " + msg + Style.RESET_ALL)

    elif (type == 'warning' and WARNING == 1):
        print(Fore.YELLOW + "(" + "{0:f}".format(ts) + ") WARNING: " +
              msg + Style.RESET_ALL)

    elif (type == 'error' and ERROR == 1):
        print(Fore.RED + "(" + "{0:f}".format(ts)
              + ") ERROR: " + msg + Style.RESET_ALL)
        # raise Exception(msg)


class ContainerGeometry(object):

    def __init__(self, index=0, diameter=0, bottomHeight=0, bottomSection=0,
                 bottomPosition=0, immersionDepth=0, leavingHeight=0, jetHeight=0,
                 startOfHeightBottomSearch=0, dispenseHeightAfterBottomSearch=0,
                 ):
        self.index = index
        self.diameter = diameter
        self.bottomHeight = bottomHeight
        self.bottomSection = bottomSection
        self.bottomPosition = bottomPosition
        self.immersionDepth = immersionDepth
        self.leavingHeight = leavingHeight
        self.jetHeight = jetHeight
        self.startOfHeightBottomSearch = startOfHeightBottomSearch
        self.dispenseHeightAfterBottomSearch = dispenseHeightAfterBottomSearch

    pass


class DeckGeometry(object):

    def __init__(self, index=None, endTraversePosition=0,
                 beginningofTipPickingPosition=0, positionofTipDepositProcess=0):
        if index is None:
            raise ValueError(
                "Cannot initialize DeckGeometry instance with unspecified index.")
        self.index = index
        self.endTraversePosition = endTraversePosition
        self.beginningofTipPickingPosition = beginningofTipPickingPosition
        self.positionofTipDepositProcess = positionofTipDepositProcess


class LiquidClass(object):

    def __init__(self, id=0, index=None, liquidClassForFilterTips=0,
                 aspirationMode=0, aspirationFlowRate=0, overAspiratedVolume=0,
                 aspirationTransportVolume=0, blowoutAirVolume=0, aspirationSwapSpeed=0,
                 aspirationSettlingTime=0, lld=0, clldSensitivity=0, plldSensitivity=0,
                 adc=0, dispensingMode=0, dispensingFlowRate=0, stopFlowRate=0,
                 stopBackVolume=0, dispensingTransportVolume=0, acceleration=0,
                 dispensingSwapSpeed=0, dispensingSettlingTime=0, flowRateTransportVolume=0):
        if index is None:
            raise ValueError(
                "Cannot initialize LiquidClass instance with unspecified index.")
        self.id = id
        self.index = index
        self.liquidClassForFilterTips = liquidClassForFilterTips
        self.aspirationMode = aspirationMode
        self.aspirationFlowRate = aspirationFlowRate
        self.overAspiratedVolume = overAspiratedVolume
        self.aspirationTransportVolume = aspirationTransportVolume
        self.blowoutAirVolume = blowoutAirVolume
        self.aspirationSwapSpeed = aspirationSwapSpeed
        self.aspirationSettlingTime = aspirationSettlingTime
        self.lld = lld
        self.clldSensitivity = clldSensitivity
        self.plldSensitivity = plldSensitivity
        self.adc = adc
        self.dispensingMode = dispensingMode
        self.dispensingFlowRate = dispensingFlowRate
        self.stopFlowRate = stopFlowRate
        self.stopBackVolume = stopBackVolume
        self.dispensingTransportVolume = dispensingTransportVolume
        self.acceleration = acceleration
        self.dispensingSwapSpeed = dispensingSwapSpeed
        self.dispensingSettlingTime = dispensingSettlingTime
        self.flowRateTransportVolume = flowRateTransportVolume


class remoteFrameListener(can.Listener):

    def __init__(self, p):
        self.parent = p
        self.remote_flag = 0
        self.waiting_for_remote_flag = 0
        self.kick_flag = 0
        self.waiting_for_kick_flag = 0
        self.data_flag = 0
        self.received_msg = ""
        self.msg_complete_flag = 0
        self.last_transmitted = ""
        self.ltMutex = Lock()
        self.rfMutex = Lock()
        self.kfMutex = Lock()
        self.msg_last = can.Message()

    def on_message_received(self, msg):
        printMSG(
            "debug", f'Received message: arbitration id = {msg.arbitration_id:X}')

        # REMOTE FRAME ACTION
        if (msg.is_remote_frame == True):
            #  if((msg.arbitration_id == 0x0000) or (msg.arbitration_id == 0x0020)):
            #  return
            if (self.getRemoteFlag() == 0):
                self.setRemoteFlag(1)
                printMSG("info", "Received remote frame with ID = {}, DLC = {}.".format(
                    self.parseMsgID(msg.arbitration_id, "s"), msg.dlc))
                #  print(Fore.BLUE + "{}".format(msg) + Style.RESET_ALL)
            return

        # Prevent handler from responding multiple times to same message
        if (msg == self.msg_last):
            printMSG("debug", 'Same message as last. Skipping.')
            return
        self.msg_last = msg

        # KICK FRAME ACTION
        #  elif(msg.arbitration_id == 0x0420):
        if ((msg.arbitration_id & KICK_MASK) or (msg.arbitration_id ==
                                                 0x0420)):
            if msg.arbitration_id == 0x0420:
                printMSG("debug", 'msg.arbitration_id == 0x0420')
            if (msg.arbitration_id == 0x0401):
                return
            if (self.getKickFlag() == 0):
                self.setKickFlag(1)
                printMSG("info", "Received Kick.")
                #  print(Fore.BLUE + "{}".format(msg) + Style.RESET_ALL)
                if self.parent.auto_response:
                    self.parent.sendRemoteFrame(1)
            return

        else:
            # Ignore the messages that we've sent out
            if self.parseMsgID(msg.arbitration_id, "r") == 1:
                return

            # print(Fore.BLUE + "{}".format(msg) + Style.RESET_ALL)
            if (self.msg_complete_flag == 1):
                self.received_msg = ""
                self.msg_complete_flag = 0

            # self.received_msg += msg.data.replace(" ", "")[:-1]
            # self.received_msg += msg.data.replace(" ", "")
            self.received_msg += msg.data[:-1].decode('iso-8859-1').replace(" ", "")

            if (self.msg_is_last(msg) == 0):
                if self.parent.auto_response:
                    self.parent.sendRemoteFrame(8)
            else:
                self.msg_complete_flag = 1
                printMSG(
                    "debug", "Assembled message {}".format(self.received_msg))
                #  if self.parent.auto_response:
                #  self.parent.sendRemoteFrame(8)

                # I'm really not sure whether the kick flag should be reset here
                self.setKickFlag(0)
                printMSG("debug", 'Kick flag is set to 0.')

                ret = self.parent.parseErrors(self.received_msg)
                if (ret != "NONE"):
                    printMSG("error", "{}".format(ret))
                    return ret

    def remote_received(self):
        if (self.remote_flag == 1):
            self.remote_flag = 0
            return 1
        else:
            return 0

    def setLastTransmitted(self, lt):
        self.ltMutex.acquire()
        lt = lt.replace("", "")
        self.last_transmitted = lt
        printMSG("warning", "Setting last transmitted to\
                {}".format(lt))
        self.ltMutex.release()

    def getLastTransmitted(self):
        self.ltMutex.acquire()
        ret = self.last_transmitted
        self.ltMutex.release()
        return ret

    def kick_received(self):
        if (self.kick_flag == 1):
            self.kick_flag = 0
            return 1
        else:
            return 0

    def data_received(self):
        if (self.data_flag == 1):
            self.data_flag = 0
            return 1
        else:
            return 0

    def msg_is_last(self, msg):
        size = len(msg.data)
        if (size > 0):
            #  printMSG(
            #  "warning", "control byte length = {}".format(len(msg.data)))
            control_byte = msg.data[(len(msg.data) - 1)]
            if ((control_byte & EOM_MASK) > 0):
                return 1

        return 0

    def parseMsgID(self, id, field):
        if field == "r":
            return id & RECEIVER_ID_MASK
        elif field == "s":
            return (id & SENDER_ID_MASK) >> 5
        else:
            return 0

    def setRemoteFlag(self, val):
        self.rfMutex.acquire()
        self.remote_flag = val
        self.rfMutex.release()

    def setKickFlag(self, val):
        self.kfMutex.acquire()
        self.kick_flag = val
        self.kfMutex.release()

    def getRemoteFlag(self):
        self.rfMutex.acquire()
        val = self.remote_flag
        self.rfMutex.release()
        return val

    def getKickFlag(self):
        self.kfMutex.acquire()
        val = self.kick_flag
        self.kfMutex.release()
        return val


def split_by_n(seq, n):
    """A generator to divide a sequence into chunks of n units."""
    while seq:
        yield seq[:n]
        seq = seq[n:]


class ZeusModule(object):
    CANBus = None
    transmission_retries = 5
    remote_timeout = 1
    errorTable = {
        "20": "No communication to EEPROM.",
        "30": "Undefined command.",
        "31": "Undefined parameter.",
        "32": "Parameter out of range.",
        "35": "Voltage outside the permitted range.",
        "36": "Emergency stop is active or was sent during action.",
        "38": "Empty liquid class.",
        "39": "Liquid class write protected.",
        "40": "Parallel processes not permitted.",
        "50": "Initialization failed.",
        "51": "Pipetting drive not initialized.",
        "52": "Movement error on pipetting drive.",
        "53": "Maximum volume of the tip reached.",
        "54": "Maximum volume in pipetting drive reached.",
        "55": "Volume check failed.",
        "56": "Conductivity check failed.",
        "57": "Filter check failed.",
        "60": "Initialization failed.",
        "61": "Z-drive is not initialized.",
        "62": "Movement error on the z-drive.",
        "63": "Container bottom search failed.",
        "64": "Z-position not possible.",
        "65": "Z-position not possible.",
        "66": "Z-position not possible.",
        "67": "Z-position not possible.",
        "68": "Z-position not possible.",
        "69": "Z-position not possible.",
        "70": "Liquid level not detected.",
        "71": "Not enough liquid present.",
        "72": "Auto calibration of the pressure sensor not possible.",
        "74": "Early liquid level detection.",
        "75": "No tip picked up or no tip present.",
        "76": "Tip already picked up.",
        "77": "Tip not discarded.",
        "80": "Clot detected during aspiration.",
        "81": "Empty tube detected during aspiration.",
        "82": "Foam detected during aspiration.",
        "83": "Clot detected during dispensing.",
        "84": "Foam detected during dispensing.",
        "85": "No communication to the digital potentiometer.",
    }

    def __init__(self, id=None, init_module=True, auto_response=True):
        # colorama.init()
        print(f"this is class __init__, id = {id}")
        init()
        self.id = id
        self.auto_response = auto_response
        if id is None:
            raise ValueError(
                "Cannot initialize ZeusModule instance with unspecified id.")
        elif id not in range(1, 32):
            raise ValueError(
                "Cannot initialize ZeusModule instance with out of range id."
                " Valid id range is [1-31]")
        self.initCANBus()
        self.pos = 0
        self.minZPosition = 0
        self.maxZPosition = 2340
        self.r = remoteFrameListener(self)
        self.remoteFrameNotifier = can.Notifier(self.CANBus, [self.r])
        # print("ZeusModule {}: initializing...".format(self.id))
        logging.info("ZeusModule {}: initializing...".format(self.id))

        if init_module:
            self.initZDrive()
            printMSG("debug", 'sleeping before initDosingDrive')
            sleep(5)
            printMSG("debug", f'Kick flag = {self.r.getKickFlag()}')
            self.initDosingDrive()
            printMSG("debug", 'sleeping after initDosingDrive')
            sleep(3)

    def setAutoResponse(self, auto):
        self.auto_response = auto

    def cmdHeader(self, command):
        # return command + "id" + str(self.id).zfill(4)
        return command + "id0000"

    def assembleIdentifier(self, msg_type, master_id=0):
        identifier = 0
        identifier |= self.id
        if (master_id > 0):
            identifier |= (master_id << 5)
        if msg_type == 'kick':
            identifier |= 1 << 10
        # print(identifier)
        return identifier

    def sendRemoteFrame(self, dlc):
        # SEND REMOTE FRAME
        msg = can.Message(
            is_extended_id=False,
            is_remote_frame=True,
            arbitration_id=0x0020)
        msg.dlc = dlc
        printMSG(
            "info", "ZeusModule {}: sending remote frame with dlc = {}...".format(self.id, msg.dlc))
        # print(Fore.GREEN + "{}".format(msg) + Style.RESET_ALL)
        try:
            self.CANBus.send(msg)
        except can.canError:
            print(
                Fore.RED + "ERROR: Remote frame not sent!" + Style.RESET_ALL)

    def waitForRemoteFrame(self):
        # WAIT FOR REMOTE RESPONSE
        # sleep(self.remote_timeout)
        s = time.time()
        c = time.time()
        # LOOP HERE UNTIL TIMEOUT EXPIRES
        while ((c - s) < self.remote_timeout):
            c = time.time()
            if (self.r.remote_received() == 1):
                printMSG("debug", f'waitForRemoteFrame: Received remote frame after {time.time()-s} s')
                # printMSG("debug", "ACK Received.")
                return 1
        return 0

    def sendKickFrame(self):
        # print('sending kick')
        n = 0
        msg = can.Message(
            is_extended_id=False,
            arbitration_id=self.assembleIdentifier('kick'), data=0)
        printMSG("info",
                 "ZeusModule, {}: sending kick frame...".format(self.id))
        #  print(Fore.GREEN + "{}".format(msg) + Style.RESET_ALL)
        while (n < self.transmission_retries):
            try:
                self.CANBus.send(msg)
            except can.canError:
                printMSG("error", "Kick not sent!")

            # WAIT FOR REMOTE RESPONSE
            if (self.waitForRemoteFrame() == 1):
                return
            if (n < self.transmission_retries):
                printMSG("warning", "Timeout waiting for kick response. Issuing retry {} of {}".format(
                    n + 1, self.transmission_retries))
            n += 1

        # Should not get here unless no response is received.
        printMSG(
            "error", "No remote frame received. Check connection to Zeus module.")
        exit(1)

    def waitForKickFrame(self):
        printMSG("debug", 'waitForKickFrame')
        # WAIT FOR REMOTE RESPONSE
        # sleep(self.remote_timeout)
        # sleep(0.001)
        s = time.time()
        c = time.time()
        # LOOP HERE UNTIL TIMEOUT EXPIRES
        while ((c - s) < self.remote_timeout):
            c = time.time()
            if (self.r.kick_received() == 1):
                printMSG("debug", "waitforkickframwe - ACK Received.")
                return 1

        return 0

    def sendDataObject(self, i, cmd_len, data):
        byte = 0
        printMSG(
            "info", "ZeusModule {}: sending data frame {} of {}...".format(self.id, i + 1, cmd_len))
        printMSG('debug', "Outstring = {}".format(data))
        printMSG(
            # "debug", "data pre append = {}".format(data.encode('hex')))
            "debug", "data pre append (hex) = {}".format(codecs.encode(data.encode(), 'hex')))
        # Assemble the 8th (status) byte
        # Add EOM bit if this is the last frame of the message.
        if (i == (cmd_len - 1)):
            printMSG("debug", "appending EOM bit to byte")
            byte |= 1 << 7
        # Add number of data bytes
        byte |= (len(data) << 4)
        printMSG("debug", "num data bytes = {}".format(len(data)))
        byte |= ((i + 1) % 31)
        printMSG("debug", "frame counter = {}".format(((i + 1) % 31)))
        printMSG("debug", "control byte (binary) = {0:b}".format(byte))
        printMSG("debug", "control byte (hex) = {0:X}".format(byte))
        # PAD FRAME WITH ZEROES
        while (len(data) < 7):
            data += " "

        # # APPEND CONTROL BYTE
        # data += chr(byte)

        # APPEND CONTROL BYTE (encodings are devil's work)
        data = bytearray(data.encode('iso-8859-1'))
        # print(data)
        data.append(byte)
        # print(data)

        printMSG(
            # "debug", "data post append = {}".format(codecs.encode(data.encode(), 'hex')))
            "debug", "data post append = {}".format(data))
        printMSG(
            # "debug", "data pre append = {}".format(data.encode('hex')))
            "debug", "data post append (hex) = {0}".format(['{0:X}'.format(x) for x in data]))
        msg = can.Message(
            is_extended_id=False,
            arbitration_id=self.assembleIdentifier('data'),
            data=data)
        # self.r.setLastTransmitted(msg.data)
        try:
            self.CANBus.send(msg)
            # print(Fore.GREEN + "{}".format(msg) + Style.RESET_ALL)

        except can.CanError as err:
            printMSG("error", "Message not sent!")
            # raise can.CanError(err)

    def sendCommand(self, cmd):
        data = list(split_by_n(cmd, 7))
        cmd_len = len(data)
        printMSG(
            "info", "ZeusModule {}: sending packet {} in {} data frame(s)...".format(self.id, cmd, cmd_len))

        # Send kick frame and wait for remote response
        self.sendKickFrame()
        for i in range(0, cmd_len):
            #        n = 0
            # outstring = bytearray(data[i])
            outstring = data[i]
            for n in range(0, self.transmission_retries):
                # SEND DATA FRAME
                self.sendDataObject(i, cmd_len, outstring)

                # WAIT FOR REMOTE RESPONSE UNLESS FRAME IS LAST IN COMMAND
                # if (int(outstring[-1]) & EOM_MASK):
                #     return

                # Yaroslav's version
                printMSG("debug", f'outstring is {outstring}')
                if i == cmd_len - 1:
                    printMSG("debug", 'This frame is last in command.')
                    return
                if (self.waitForRemoteFrame() == 1):
                    printMSG("debug", 'Received remote frame')
                    break
                else:
                    printMSG("warning", "Timeout waiting for remote response. Issuing retry {} of {}".format(
                        n + 1, self.transmission_retries))
        self.waitForKickFrame()


    def initCANBus(self):
        printMSG(
            "info", "ZeusModule {}: initializing CANBus...".format(self.id))
        can.rc['interface'] = 'kvaser'
        can.rc['channel'] = '0'
        can.rc['bitrate'] = 500000
        self.CANBus = can.interface.Bus()
        #  self.CANBus = can.interface.Bus(can_filters=[{"can_id": 0x01,
        #  "can_mask": 0xFF}])

    def initDosingDrive(self):
        cmd = self.cmdHeader('DI')
        printMSG(
            "info", "ZeusModule {}: initializing dosing drive...".format(self.id))
        self.sendCommand(cmd)

    def initZDrive(self):
        cmd = self.cmdHeader('ZI')
        printMSG(
            "info", "ZeusModule {}: initializing z-drive...".format(self.id))
        self.pos = self.maxZPosition
        self.sendCommand(cmd)

    def moveZDrive(self, pos, speed):
        cmd = self.cmdHeader('GZ')
        if (pos > self.maxZPosition) or (pos < self.minZPosition):
            raise ValueError(
                "ZeusModule {}: requested z-position out of range. "
                " Valid range for z-position is between {} and {}"
                    .format(self.id, self.minZPosition, self.maxZPosition))
        if (speed == "slow"):
            speed = 0
        elif (speed == "fast"):
            speed = 1
        else:
            raise ValueError(
                "ZeusModule {}: invalid z-axis drive speed specified."
                " Accepted values for z-axis drive speed are \'slow\'"
                " and \'fast\'.")
        print(
            "ZeusModule {}: moving z-drive from position {} to position {}."
                .format(self.id, self.pos, pos))
        cmd = cmd + 'gy' + str(pos).zfill(4) + 'gw' + str(speed)
        self.pos = pos
        self.sendCommand(cmd)

    def pickUpTip(self, tipTypeTableIndex, deckGeometryTableIndex):
        cmd = self.cmdHeader('GT')
        cmd = cmd + 'tt' + str(tipTypeTableIndex).zfill(
            2) + 'go' + str(deckGeometryTableIndex).zfill(2)

        self.sendCommand(cmd)

    def discardTip(self, deckGeometryTableIndex):
        cmd = self.cmdHeader('GU')
        cmd = cmd + 'go' + str(deckGeometryTableIndex).zfill(2)
        self.sendCommand(cmd)

    def sendString(self, string):
        # cmd = self.cmdHeader(string)
        self.sendCommand(string)

    def aspiration(self, aspirationVolume=0, containerGeometryTableIndex=0,
                   deckGeometryTableIndex=0, liquidClassTableIndex=0, qpm=0,
                   lld=0, lldSearchPosition=0, liquidSurface=0, mixVolume=0,
                   mixFlowRate=0, mixCycles=0):
        cmd = self.cmdHeader('GA')
        cmd = cmd + 'ai' + str(aspirationVolume).zfill(5) + \
              'ge' + str(containerGeometryTableIndex).zfill(2) + \
              'go' + str(deckGeometryTableIndex).zfill(2) + \
              'lq' + str(liquidClassTableIndex).zfill(2) + \
              'gq' + str(qpm) + \
              'lb' + str(lld) + \
              'zp' + str(lldSearchPosition).zfill(4) + \
              'cf' + str(liquidSurface).zfill(4) + \
              'ma' + str(mixVolume).zfill(5) + \
              'mb' + str(mixFlowRate).zfill(5) + \
              'dn' + str(mixCycles).zfill(2)
        self.sendCommand(cmd)

    def dispensing(self, dispensingVolume=0, containerGeometryTableIndex=0,
                   deckGeometryTableIndex=0, qpm=0, liquidClassTableIndex=0,
                   lld=0, lldSearchPosition=0, liquidSurface=0,
                   searchBottomMode=0, mixVolume=0, mixFlowRate=0, mixCycles=0):
        cmd = self.cmdHeader('GD')
        cmd = cmd + 'di' + str(dispensingVolume).zfill(5) + \
              'ge' + str(containerGeometryTableIndex).zfill(2) + \
              'go' + str(deckGeometryTableIndex).zfill(2) + \
              'gq' + str(qpm) + \
              'lq' + str(liquidClassTableIndex).zfill(2) + \
              'lb' + str(lld) + \
              'zp' + str(lldSearchPosition).zfill(4) + \
              'cf' + str(liquidSurface).zfill(4) + \
              'zm' + str(searchBottomMode) + \
              'ma' + str(mixVolume).zfill(5) + \
              'mb' + str(mixFlowRate).zfill(5) + \
              'dn' + str(mixCycles).zfill(2)
        self.sendCommand(cmd)

    def switchOff(self):
        cmd = self.cmdHeader('AV')
        self.sendCommand(cmd)

    def calculateContainerVolume(self, containerGeometryTableIndex=0,
                                 deckGeometryTableIndex=0,
                                 liquidClassTableIndex=0, lld=0,
                                 lldSearchPosition=0, liquidSurface=0):
        cmd = self.cmdHeader('GJ')
        cmd = cmd + 'ge' + str(containerGeometryTableIndex).zfill(2) + \
              'go' + str(deckGeometryTableIndex).zfill(2) + \
              'lq' + str(liquidClassTableIndex).zfill(2) + \
              'lb' + str(lld) + \
              'zp' + str(lldSearchPosition).zfill(4) + \
              'cf' + str(liquidSurface).zfill(3)
        self.sendCommand(cmd)

    def calculateContainerVolumeAfterPipetting(self):
        cmd = self.cmdHeader('GN')
        self.sendCommand(cmd)

    def getErrorCode(self):
        cmd = self.cmdHeader('RE')
        self.sendCommand(cmd)

    def getFirmwareVersion(self):
        # cmd = self.cmdHeader('RF')
        self.sendCommand("RF")
        # self.sendCommand(cmd)

    def getParameterValue(self, parameterName):
        if (len(parameterName) > 2):
            raise ValueError(
                "ZeusModule {}: Invalid parameter \'{}\' requested. "
                " Parameter format must be two lower-case letters."
                    .format(parameterName))
        cmd = self.cmdHeader('RA')
        cmd = cmd + 'ra' + parameterName
        self.sendCommand(cmd)

    def getInstrumentInitializationStatus(self):
        cmd = self.cmdHeader('QW')
        self.sendCommand(cmd)

    def getNameofLastFaultyParameter(self):
        cmd = self.cmdHeader('VP')
        self.sendCommand(cmd)

    def getTipPresenceStatus(self):
        cmd = self.cmdHeader('RT')
        self.sendCommand(cmd)

    def getTechnicalStatus(self):
        cmd = self.cmdHeader('QT')
        self.sendCommand(cmd)

    def getAbsoluteZPosition(self):
        cmd = self.cmdHeader('RZ')
        self.sendCommand(cmd)

    def getCycleCounter(self):
        cmd = self.cmdHeader('RV')
        self.sendCommand(cmd)

    def getLifetimeCounter(self):
        cmd = self.cmdHeader('RY')
        self.sendCommand(cmd)

    def getInstrumentStatus(self):
        cmd = self.cmdHeader('RQ')
        self.sendCommand(cmd)
        pass

    def getLiquidClassRevision(self):
        cmd = self.cmdHeader('XB')
        self.sendCommand(cmd)
        pass

    def setEmergencyStop(self, state):
        if state in set([1, 'on', 'ON', 'True', 'true']):
            cmd = self.cmdHeader('AB')
        if state in set([0, 'off', 'OFF', 'False', 'false']):
            cmd = seld.cmdHeader('AW')
        self.sendCommand(cmd)

    def switchDigitalOutput(self, out1State, out2State):
        cmd = self.cmdHeader('OU')
        cmd += 'ou'
        if out1State in set([1, 'on', 'ON', 'True', 'true']):
            cmd += str(1)
        if out2State in set([0, 'off', 'OFF', 'False', 'false']):
            cmd += str(0)

        cmd += 'oy'
        if out2State in set([1, 'on', 'ON', 'True', 'true']):
            cmd += str(1)
        if out2State in set([0, 'off', 'OFF', 'False', 'false']):
            cmd += str(0)

    def switchLEDStatus(self, blueState, redState):
        if (blueState not in set([0, 1])) or (redState not in set([0, 1])):
            raise ValueError(
                "ZeusModule {}: requested LED state out of range. "
                " Valid range for LED state is [0,1]".format(self.id))
        cmd = self.cmdHeader('SL')
        cmd += 'sl' + str(blueState) + \
               'sk' + str(redState)
        print("Switching status of blue LED to {} and red LED to {}"
              .format(blueState, redState))
        self.sendCommand(cmd)

    def testModeCommand(self, status):
        if (status not in set([0, 1])):
            raise ValueError(
                "ZeusModule {}: requested LED state out of range. "
                " Valid range for LED state is [0,1]".format(self.id))
        cmd = self.cmdHeader('AT')
        cmd += 'at' + str(status)
        self.sendCommand(cmd)

    def setDosingDriveInCleaningPosition(self):
        cmd = self.cmdHeader('GX')
        self.sendCommand(cmd)

    def setContainerGeometryParameters(self, containerGeometryParameters):
        cmd = self.cmdHeader('GC')
        cmd = cmd + 'ge' + str(containerGeometryParameters.index).zfill(2) + \
              'cb' + str(containerGeometryParameters.diameter).zfill(3) + \
              'bg' + str(containerGeometryParameters.bottomHeight).zfill(4) + \
              'gx' + str(containerGeometryParameters.bottomSection).zfill(5) + \
              'ce' + str(containerGeometryParameters.bottomPosition).zfill(4) + \
              'ie' + str(containerGeometryParameters.immersionDepth).zfill(4) + \
              'yq' + str(containerGeometryParameters.leavingHeight).zfill(4) + \
              'yr' + str(containerGeometryParameters.jetHeight).zfill(4) + \
              'ch' + \
              str(containerGeometryParameters.startOfHeightBottomSearch).zfill(4) + \
              'ci' + \
              str(containerGeometryParameters.dispenseHeightAfterBottomSearch).zfill(
                  4)
        self.sendCommand(cmd)

    def getContainerGeometryParameters(self, index):
        if index is None:
            raise ValueError(
                "Please specify a valid container geometry table index.")
        cmd = self.cmdHeader('GB')
        cmd = cmd + 'ge' + str(index).zfill(2)
        ret = ContainerGeometry(index=index)
        # Request and fill class attributes here
        return ret

    def setDeckGeometryParameters(self, deckGeometryParameters):
        cmd = self.cmdHeader('GO')
        cmd = cmd + 'go' + str(deckGeometryParameters.index).zfill(2) + \
              'te' + str(deckGeometryParameters.endTraversePosition).zfill(4) + \
              'tm' + \
              str(deckGeometryParameters.beginningofTipPickingPosition).zfill(4) + \
              'tr' + \
              str(deckGeometryParameters.positionofTipDepositProcess).zfill(
                  4)
        self.sendCommand(cmd)

    def getDeckGeometryParameters(self, index):
        if index is None:
            raise ValueError(
                "Please specify a valid deck geometry table index.")
        cmd = self.cmdHeader('GR')
        cmd = cmd + 'go' + str(index).zfill(2)
        self.sendCommmand(cmd)

    def setLiquidClassParameters(self, liquidClassParameters):
        if liquidClassParameters.index is None:
            raise ValueError(
                "Please specify a valid deck geometry table index.")
        cmd = self.cmdHeader('GL')
        cmd = cmd + 'id' + str(liquidClassParameters.id).zfill(4) + \
              'lq' + str(liquidClassParameters.index).zfill(2) + \
              'uu' + str(liquidClassParameters.liquidClassForFilterTips) + \
              str(liquidClassParameters.aspirationMode) + \
              str(liquidClassParameters.aspirationFlowRate).zfill(5) + \
              str(liquidClassParameters.overAspiratedVolume).zfill(4) + \
              str(liquidClassParameters.aspirationTransportVolume).zfill(5) + \
              str(liquidClassParameters.blowoutAirVolume).zfill(5) + \
              str(liquidClassParameters.aspirationSwapSpeed).zfill(4) + \
              str(liquidClassParameters.aspirationSettlingTime).zfill(3) + \
              str(liquidClassParameters.lld) + \
              str(liquidClassParameters.clldSensitivity) + \
              str(liquidClassParameters.plldSensitivity) + \
              str(liquidClassParameters.adc) + \
              str(liquidClassParameters.dispensingMode) + \
              str(liquidClassParameters.dispensingFlowRate).zfill(5) + \
              str(liquidClassParameters.stopFlowRate).zfill(5) + \
              str(liquidClassParameters.stopBackVolume).zfill(3) + \
              str(liquidClassParameters.dispensingTransportVolume).zfill(5) + \
              str(liquidClassParameters.acceleration).zfill(3) + \
              str(liquidClassParameters.dispensingSwapSpeed).zfill(4) + \
              str(liquidClassParameters.dispensingSettlingTime).zfill(3) + \
              str(liquidClassParameters.flowRateTransportVolume).zfill(5)
        self.sendCommand(cmd)

    def getLiquidClassParameters(self, id, index):
        cmd = self.cmdHeader('GM')
        cmd = cmd + 'id' + str(id).zfill(4) + \
              'iq' + str(index).zfill(2)
        self.sendCommand(cmd)

    def firmwareUpdate(self, filename):
        pass

    def parseErrors(self, errorString):
        if len(errorString.replace(" ", "")) == 0:
            return "NONE"
        if errorString == "":
            return "NONE"

        printMSG("warning", "ErrorString = {}".format(errorString))

        #  else:
        # print(Fore.MAGENTA + "DEBUG: Received error string '{}' with
        # length: {}".format(errorString, len(errorString.replace(" ",
        # ""))) + Style.RESET_ALL)

        cmd = str(errorString[:2])
        # print("cmd = {}".format(cmd))
        eidx = errorString.find("er")
        if (eidx == -1):
            return "NONE"

        ec = str(errorString[(eidx + 2): (eidx + 4)])
        if ec == '00':
            # NO ERROR
            return
        #  print(Fore.MAGENTA + "DEBUG: ec = {}".format(ec))

        defaultError = "Unknown error code returned."
        if cmd == 'DI':
            if ec in set(['00', '30', '35', '36', '40', '50', '52']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'ZI':
            if ec in set(['00', '30', '35', '36', '40', '60', '62']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GZ':
            if ec in set(['00', '31', '32', '35', '36', '40', '61', '62', '64']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GT':
            if ec in set(['00', '31', '32', '35', '36', '40', '51', '52', '61',
                          '62', '65', '75', '76']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GU':
            if ec in set(['00', '30', '31', '32', '35', '36', '40', '51', '52',
                          '61', '62', '65', '69', '75', '77']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GA':
            if ec in set(['00', '30', '31', '32', '35', '36', '38', '40', '51',
                          '52', '53', '54', '55', '56', '57', '61', '62', '65',
                          '66', '67', '68', '70', '71', '72', '74', '75', '80',
                          '81', '82', '85']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GD':
            if ec in set(['00', '30', '31', '32', '35', '36', '38', '40', '51',
                          '52', '54', '55', '57', '61', '62', '63', '65', '66',
                          '67', '68', '70', '72', '74', '75', '83', '84', '85']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GJ':
            if ec in set(['00', '30', '31', '32', '35', '36', '38', '40', '51',
                          '52', '56', '57', '61', '62', '65', '66', '67', '68',
                          '70', '72', '74', '85']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'AB':
            if ec in set(['00', '30']):
                return self.errorTable[ec]
            else:
                return defaultError
        elif cmd == 'AW':
            if ec in set(['00', '30']):
                return self.errorTable[ec]
            else:
                return defaultError
        elif cmd == 'XA':
            if ec in set(['00', '20', '30', '31', '32']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GK':
            if ec in set(['00', '30', '31', '32', '35', '51', '52', '54']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GC':
            if ec in set(['00', '20', '30', '31', '32']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GO':
            if ec in set(['00', '20', '30', '31', '32']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GB':
            if ec in set(['00', '20', '30', '31', '32']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GR':
            if ec in set(['00', '20', '30', '31', '32']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GL':
            if ec in set(['00', '20', '30', '31', '32', '39']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GM':
            if ec in set(['00', '20', '30', '31', '32']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GQ':
            if ec in set(['00', '20', '30', '31', '32']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GS':
            if ec in set(['00', '20', '30', '31', '32']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GV':
            if ec in set(['00', '20', '30', '31', '32']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GW':
            if ec in set(['00', '20', '30', '31', '32']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GG':
            if ec in set(['00', '20', '30', '31', '32']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GE':
            if ec in set(['00', '20', '30', '31', '32']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GH':
            if ec in set(['00', '20', '30', '31', '32']):
                return self.errorTable[ec]
            else:
                return defaultError

        elif cmd == 'GI':
            if ec in set(['00', '20', '30', '31', '32']):
                return self.errorTable[ec]
            else:
                return defaultError
        else:
            return "Error code returned '{}' corresponds to unknown command.".format(errorString)
