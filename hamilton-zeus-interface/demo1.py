# TESTS AND DEMOS CAN BE IN SEPARATE FILES LIKE THIS:
import zeuslt


zeus = zeuslt.ZeusLTModule(id=815, COMport='COM5', COM_timeout=0.1)
zeus.firmware_version()