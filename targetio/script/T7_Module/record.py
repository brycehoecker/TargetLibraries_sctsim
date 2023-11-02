import target_driver
import target_io
import time

def record(outFile, runDuration=1):
    #Make connections
    my_ip = "192.168.1.2"
    tb_ip = "192.168.1.173"
    board_ip = "192.168.0.173"

    tester = target_driver.TesterBoard()
    print tester.ConnectToServer(my_ip, 8103, tb_ip, 8104)
    time.sleep(0.1)
    tester.EnableReset(True)
    time.sleep(0.1)
    tester.EnableReset(False)
    time.sleep(0.1)

    board_def = ("/Users/pkarn/TargetDriver/config/"
        "TM7_FPGA_Firmware0xFEDB0007.def")
    asic_def = "/Users/pkarn/TargetDriver/config/TM7_ASIC.def"

    board = target_driver.TargetModule(board_def, asic_def, 1)

    print board.ConnectToServer(my_ip,8201,board_ip,8105)
    #board.WriteSetting("SetSlowControlPort", 8201)
    #board.WriteSetting("SetDataPort", 8107)
    #second arg: +module id defined in target_driver.TargetModule (last arg)

    #Set Vped, enable all channels for readout
    print board.WriteSetting("Vped_value", 1000)
    board.WriteSetting("EnableChannelsASIC0", 0xffff)
    board.WriteSetting("EnableChannelsASIC1", 0xffff)
    board.WriteSetting("EnableChannelsASIC2", 0xffff)
    board.WriteSetting("EnableChannelsASIC3", 0xffff)
    board.WriteSetting("Zero_Enable", 0x1)

    #Use 14 buffers = 448 ns
    board.WriteSetting("NumberOfBlocks", 13)

    #Set trigger delay
    board.WriteSetting("TriggerDelay", 8)

    #HV Control
    #Start MAX11616, HV monitoring
    print board.WriteRegister(0x1F, 0x80000000)
    print board.WriteSetting("HV_Enable", 0x0)
    time.sleep(0.1)
    print board.WriteSetting("HV_Enable", 0x1)

    time.sleep(0.1)
    #Set reference voltage to 4.096V, need to do twice?
    board.WriteRegister(0x20, 0x7300080F)
    board.WriteRegister(0x20, 0x7300080F)
    time.sleep(1)
    #Set low side voltage for all trigger channels to 2.048V
    board.WriteRegister(0x20, 0x8280080F)

    kNPacketsPerEvent = 64 #One per channel
    #if multiple channels depend on FPGA settings
    kPacketSize = 918#you can read it on wireshark
    # check for data size in bytes
    kBufferDepth = 3000

    #Set up IO
    listener = target_io.DataListener(kBufferDepth, kNPacketsPerEvent, kPacketSize)
    #target_driver.TargetModule.DataPortPing(my_ip, board_ip)#akira's hack
    my_ip = "192.168.1.2"
    listener.AddDAQListener(my_ip)
    listener.StartListening()

    writer = target_io.EventFileWriter(outFile, kNPacketsPerEvent, kPacketSize)
    buf = listener.GetEventBuffer()

    #Enable external trigger
    tester.EnableExternalTrigger(True)

    writer.StartWatchingBuffer(buf)

    #Taking data now
    time.sleep(runDuration)

    writer.StopWatchingBuffer()

    #Stop trigger
    tester.EnableExternalTrigger(False)

    print board.WriteSetting("HV_Enable", 0x0)
    #Close everything
    board.CloseSockets()
    tester.CloseSockets()
    buf.Flush()
    writer.Close()
