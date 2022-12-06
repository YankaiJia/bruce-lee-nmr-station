import zeus
# import ezstepper
from time import sleep

zm = zeus.ZeusModule(id = 1)
# zm.getFirmwareVersion()

# ez = ezstepper.EZStepper(1)

# zm.initCANBus()


# def demo():
#     # ez.setVelocity(3)
#     zm.moveZDrive(0, "fast")
#     # ez.moveAbsolute(0)
#     sleep(1)
#     zm.moveZDrive(1000, "fast")
#     for i in range(0, 6):
#         zm.moveZDrive(1400, "fast")
#         zm.moveZDrive(1500, "slow")
#         zm.moveZDrive(1000, "fast")
#         # ez.moveRelative(14.5)
#         sleep(1)
#     zm.moveZDrive(1400, "fast")
#     zm.moveZDrive(1500, "slow")
#     zm.moveZDrive(1000, "fast")
#     # ez.moveAbsolute(0)
#     zm.moveZDrive(0, "slow")
#
# if __name__ == '__main__':
#     demo()


# deckgeom = zeus.DeckGeometry(index=0, endTraversePosition=1100, beginningofTipPickingPosition=1490, positionofTipDepositProcess=800)
# zm.setDeckGeometryParameters(deckGeometryParameters=deckgeom)
# zm.pickUpTip(tipTypeTableIndex=2, deckGeometryTableIndex=0)
# container = zeus.ContainerGeometry(index=0, diameter=200, bottomHeight=0, bottomSection=10000,
#                  bottomPosition=1800, immersionDepth=50, leavingHeight=100, jetHeight=100,
#                  startOfHeightBottomSearch=100, dispenseHeightAfterBottomSearch=50,
#                  )
# zm.setContainerGeometryParameters(containerGeometryParameters=container)
# zm.aspiration(aspirationVolume=100, containerGeometryTableIndex=0,
#                    deckGeometryTableIndex=0, liquidClassTableIndex=0, qpm=0,
#                    lld=0, lldSearchPosition=0, liquidSurface=1600, mixVolume=0,
#                    mixFlowRate=0, mixCycles=0)
# zm.dispensing(dispensingVolume=100, containerGeometryTableIndex=0,
#                    deckGeometryTableIndex=0, qpm=0, liquidClassTableIndex=0,
#                    lld=0, lldSearchPosition=0, liquidSurface=1600,
#                    searchBottomMode=0, mixVolume=0, mixFlowRate=0, mixCycles=0)
#
# # LLD tests
# container = zeus.ContainerGeometry(index=0, diameter=200, bottomHeight=0, bottomSection=10000,
#                  bottomPosition=1800, immersionDepth=50, leavingHeight=100, jetHeight=1000,
#                  startOfHeightBottomSearch=100, dispenseHeightAfterBottomSearch=50,
#                  )
# zm.setContainerGeometryParameters(containerGeometryParameters=container)
# liquid_volume = 100
# zm.aspiration(aspirationVolume=liquid_volume, containerGeometryTableIndex=0,
#                    deckGeometryTableIndex=0, liquidClassTableIndex=0, qpm=1,
#                    lld=1, lldSearchPosition=1500, liquidSurface=1700, mixVolume=0,
#                    mixFlowRate=0, mixCycles=0)
#
# zm.dispensing(dispensingVolume=liquid_volume, containerGeometryTableIndex=0,
#                    deckGeometryTableIndex=0, qpm=1, liquidClassTableIndex=0,
#                    lld=0, lldSearchPosition=0, liquidSurface=1700,
#                    searchBottomMode=0, mixVolume=0, mixFlowRate=0, mixCycles=0)
