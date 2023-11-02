import target_driver
import target_io
import time

my_ip = "192.168.12.1"
module_ip = "192.168.12.173"
initialize = True

module_def = "/home/target5/Software/TargetDriver/trunk/config/SCT_MSA_FPGA_Firmware0xC0000001.def"

asic_def = "/home/target5/Software/TargetDriver/trunk/config/TC_ASIC.def"
trigger_asic_def = "/home/target5/Software/TargetDriver/trunk/config/T5TEA_ASIC.def"

module = target_driver.TargetModule(module_def, asic_def, trigger_asic_def, 0)
if initialize:
    module.EstablishSlowControlLink(my_ip, module_ip)
    module.Initialise()
    module.EnableDLLFeedback()
    print ("module initialized")
else:
    module.ReconnectToServer(my_ip, 8201, module_ip, 8105)

ret, fw = module.ReadRegister(0)
print ("Firmware version: {:x}".format(fw))



for asic in range(4):
    module.WriteSetting("EnableChannelsASIC{}".format(asic), 0xffff)
module.WriteSetting("Zero_Enable", 0x0)
module.WriteSetting("DoneSignalSpeedUp",0)
nblocks = 2
kNPacketsPerEvent = 4
module.WriteSetting("NumberOfBlocks", nblocks-1)
module.WriteSetting("MaxChannelsInPacket", int(64/kNPacketsPerEvent))

module.WriteSetting("TACK_TriggerType", 0x0)
module.WriteSetting("TACK_TriggerMode", 0x0)

#module.WriteSetting("SetPushPort", 0x200A)

#print ("\nEnabling Slow ADCs\n")
#module.WriteSetting("SlowADCEnable_Primary",0)
#time.sleep(0.05)
#module.WriteSetting("SlowADCEnable_Aux",0)
##module.WriteSetting("Event_Delay",100)

# by default we have a data packet for each channel, this can be changed




#kPacketSize = target_driver.DataPacket_CalculatePacketSizeInBytes(int(64/kNPacketsPerEvent), 32 * (nblocks))
#kBufferDepth = 10000

#listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
#listener.AddDAQListener(my_ip)
#listener.StartListening()
#writer = target_io.EventFileWriter("lol_r0.tio", kNPacketsPerEvent, kPacketSize)
#buf = listener.GetEventBuffer()
#writer.StartWatchingBuffer(buf)
for i in range (5):
    ret, current = module.ReadHVCurrentInput()
    #ret, current = module.ReadHVCurrentInput()
    print("current",current)
    time.sleep(0.01)
    #ret, voltage = module.ReadHVVoltageInput()
    ret, voltage = module.ReadHVVoltageInput()
    print("voltage",voltage)
    time.sleep(0.01)
    ret, temp =  module.GetTempI2CPrimary()
    time.sleep(0.01)
    print ("Temperature Pri: ",temp)
    ret, temp =  module.GetTempI2CAux()
    print ("Temperature Aux: ",temp)
    time.sleep(1)


exit()

#print("Packet size should be",kPacketSize)

#module.WriteSetting("HV_enable",0)
#ret,temp =  module.GetTempI2CPrimary()
#print ("Temperature Pri: ",temp)
#ret, temp =  module.GetTempI2CAux()
#print ("Temperature Aux: ",temp)
#module.WriteSetting("ExtTriggerDirection", 0x1) # hardsync
#module.WriteSetting("TACK_EnableTrigger", 0x00000)

exit()

#time.sleep(5)
#module.WriteSetting("TACK_EnableTrigger", 0x0)
#time.sleep(30)
#lsw_prev=0
#msw_prev=0
#lsw_aux_prev=0
#msw_aux_prev=0
#for i in range(20) :
    #ret, lsw = module.ReadSetting("SlowResultTimestamp_LSW_Primary")
    #ret, msw = module.ReadSetting("SlowResultTimestamp_MSW_Primary")
    #ret, lsw_aux = module.ReadSetting("SlowResultTimestamp_LSW_Aux")
    #ret, msw_aux = module.ReadSetting("SlowResultTimestamp_MSW_Aux")
    #if ((msw*2**32+lsw)-(msw_prev*2**32+lsw_prev) > 0):
        #print ("Delta Pri t:", ((msw*2**32+lsw))-((msw_prev*2**32+lsw_prev)))
        #print ("Primary Timestamp:", (msw*2**32+lsw)/1e9  , "MSW:",msw,"LSW:",lsw)
    #if ((msw_aux*2**32+lsw_aux)-(msw_aux_prev*2**32+lsw_aux_prev) > 0):
        #print ("Delta Aux t:", ((msw_aux*2**32+lsw_aux))-((msw_aux_prev*2**32+lsw_aux_prev)))
        #print ("Aux Timestamp:", (msw_aux*2**32+lsw_aux)/1e9  , "MSW:",msw_aux,"LSW:",lsw_aux)
    #lsw_prev=lsw
    #msw_prev=msw
    #lsw_aux_prev=lsw_aux
    #msw_aux_prev=msw_aux
    ##ret, lsw = module.ReadSetting("SlowResultTimestamp_LSW_Aux")
    ##ret, msw = module.ReadSetting("SlowResultTimestamp_MSW_Aux")
    ##print ("Aux MSW:",msw,"LSW:",lsw/1e9)
    #time.sleep(0.05)
#module.WriteSetting("TACK_EnableTrigger", 0x0)

#module.WriteSetting("SlowADCEnable_Primary",0)
#module.WriteSetting("SlowADCEnable_Aux",0)

module.CloseSockets()
