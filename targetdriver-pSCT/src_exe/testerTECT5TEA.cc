/*! \file */
/*!
 @file
 @brief Executable to test the TargetModule driver library
 */

#include <sys/socket.h>
#include <unistd.h>

#include "TargetDriver/DataPacket.h"
#include "TargetDriver/ModuleSimulator.h"
#include "TargetDriver/RegisterSettings.h"
#include "TargetDriver/TargetModule.h"
#include "TargetDriver/TesterBoard.h"
#include "TargetDriver/Waveform.h"

using namespace std;
using namespace CTA::TargetDriver;

int main() {
  // Specify your ip and ip of TCEvalBoard, at the moment the ip is always .123

  std::string my_ip = "192.168.0.1";
  std::string tm_ip = "192.168.0.123";
  std::string configPathFPGA =
      "/home/cta/TARGET/TargetDriver/config/"
      "TECT5TEA_FPGA_Firmware0xFEDA0008.def";
  std::string configPathASIC =
      "/home/cta/TARGET/TargetDriver/config/TEC_ASIC.def";
  std::string configPathTriggerASIC =
      "/home/cta/TARGET/TargetDriver/config/T5TEA_ASIC.def";
  int stat;

  // Establish communication with the real or simulated TM (also set FPGA
  // registers)
  TargetModule tm(configPathFPGA, configPathASIC, configPathTriggerASIC);
  cout << "Instance Ready" << endl;
  stat = tm.EstablishSlowControlLink(my_ip, tm_ip);
  if (stat != TC_OK) {
    std::cout << "EstablishSlowControlLink() failed : "
              << tm.ReturnCodeToString(stat) << std::endl;
    exit(-1);
  }

  // Try to readout firmware
  uint32_t firmware;
  tm.ReadRegister(0x0, firmware);
  std::cout << "Firmware Version: " << std::hex << firmware << std::endl;

  // Initialise TCEvalBoard with default settings
  stat = tm.Initialise();
  if (stat != TC_OK) {
    std::cout << "Init failed : " << tm.ReturnCodeToString(stat) << std::endl;
    exit(-1);
  }
  stat = tm.EnableDLLFeedback();
  if (stat != TC_OK) {
    std::cout << "EnableDLLFeedback failed : " << tm.ReturnCodeToString(stat)
              << std::endl;
    exit(-1);
  }

  // Enable synchronous trigger mode
  stat = tm.WriteSetting("TriggerDelay", 100);
  tm.WriteSetting("TACK_TriggerType", 0x0);
  tm.WriteSetting("TACK_TriggerMode", 0x0);
  tm.WriteSetting("TACK_EnableTrigger", 0x10000);
  // Set Vped
  tm.WriteSetting("Vped_value", 2000);
  // Enable one channel (Channel 0) and enable zero supression
  tm.WriteSetting("EnableChannelsASIC0", 0x1);
  tm.WriteSetting("Zero_Enable", 0x1);
  // Specify number of blocks to read out (for this iteration of the firmware,
  // the last block is not usable)
  tm.WriteSetting("NumberOfBlocks", 3);
  // Switch on trigger
  stat = tm.WriteSetting("ExtTriggerDirection", 0x1);

  // Akiras hack
  TargetModule::DataPortPing(my_ip, tm_ip);

  // Add DAQ Listener on Port 8107
  stat = tm.AddDAQListener(my_ip);
  if (stat != TC_OK) {
    std::cout << "AddDAQListener() failed : " << tm.ReturnCodeToString(stat)
              << std::endl;
    exit(-1);
  }

  // Take 5 Events
  for (int i = 0; i < 5; ++i) {
    usleep(10000);
    uint8_t d[10000];
    uint32_t bytes;
    std::cout << "Getting Data Packet " << std::endl;
    if ((stat = tm.GetDataPacket(&d, bytes, 10000)) != TC_OK) {
      std::cout << "GetDataPacket returned: " << tm.ReturnCodeToString(stat)
                << std::endl;
    } else {
      std::cout << "Received data packet with " << bytes << " bytes "
                << std::endl;
      DataPacket prec;
      prec.Assign(d, static_cast<uint16_t>(bytes));
      Waveform* w = prec.GetWaveform(0);

      std::cout << "Some ADC values"
                << " " << static_cast<double>(w->GetADC(0)) << " "
                << static_cast<double>(w->GetADC(10)) << std::endl;
    }
  }

  std::cout << "Done sampling ASIC stuff" << std::endl;

  // tm.WriteSetting("TriggerEff_Enable",1);
  // // Switch off trigger
  // stat=tm.WriteSetting("ExtTriggerDirection", 0x0);
  // uint32_t t = 0;

  // int TRG_THRES_0 = 2865;
  // int PMTREF4_0 = 1980;

  // tm.WriteTriggerASICSetting("PMTref4_0", 0, PMTREF4_0,true);
  // tm.WriteTriggerASICSetting("Thresh_0", 0, TRG_THRES_0,true);
  // tm.WriteTriggerASICSetting("TTbias_A", 0, 400,true);
  // //tm.WriteTriggerASICSetting("Vped_0", 0, 1000,true);

  // tm.WriteSetting("TriggerCounterReset", 1);
  // tm.WriteSetting("TriggerEff_Duration", 12500000); //time in 8ns -> 0.1s
  // usleep(10000);
  // uint32_t done = 0 ;
  // while(done == 0){
  //   tm.ReadSetting("TriggerEff_DoneBit",done);
  //  usleep(5000);
  // }

  // double voltage=1;

  // tm.ReadSetting("TriggEffCounter",t);
  // t = t-1;

  // usleep(50000);
  // float eff = double(t)/100.0;
  // std::cout << std::dec << voltage << "\t" << t << "\t" << eff << std::endl;

  // std::cout << "Done trigger ASIC stuff" << std::endl;

  // Close all Sockets
  tm.CloseSockets();

  return 0;
}
