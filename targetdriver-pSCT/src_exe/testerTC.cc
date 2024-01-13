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

  std::string my_ip = "192.168.12.1";
  std::string tm_ip = "192.168.12.100";
  std::string configPathFPGA =
      "/home/cta/Software/TargetDriver/trunk/config/"
      "TC_M_FPGA_Firmware0xC0000008.def";
  std::string configPathASIC =
      "/home/cta/Software/TargetDriver/trunk/config/TC_ASIC.def";
  int stat;

  // Establish communication with the real or simulated TM (also set FPGA
  // registers)
  TargetModule tm(configPathFPGA.c_str(), configPathASIC.c_str());

  //  stat = tm.Exists(tm_ip.c_str(), my_ip.c_str());

  tm.SetVerbose();

  stat = tm.EstablishSlowControlLink(my_ip.c_str(), tm_ip.c_str());
  if (stat != TC_OK) {
    uint32_t fullReg = 99;
    stat = tm.ReadRegister(0x0, fullReg);

    std::cout << "FW " << fullReg << " " << stat << std::endl;

    tm.WriteSetting("PhaseOfCommsClock", 0);
    usleep(100000);

    stat = tm.ReadRegister(0x0, fullReg);

    std::cout << "FW2 " << fullReg << " " << stat << std::endl;

    // tm.WriteSetting("PhaseOfCommsClock", 1);

    // usleep(100000);

    // stat = tm.ReadRegister(0x0, fullReg);

    // std::cout << "FW3 " << fullReg <<  " " << stat << std::endl;

    // tm.WriteSetting("PhaseOfCommsClock", 0);

    // std::cout << "EstablishSlowControlLink() failed : " <<
    // tm.ReturnCodeToString(stat) << std::endl; exit(-1);
  }
  // uint8_t val1;
  // tm.ReadModuleIP(val1);
  // stat=tm.ModifyModuleIP(173);
  // uint8_t val;
  // tm.ReadModuleIP(val);
  // std::cout << "IP before: " << (int)val1 << " stat: " << stat << " IP: " <<
  // (int)val << std::endl;

  uint8_t val;
  tm.ReadModuleIP(val);
  std::cout << "IP: " << (int)val << std::endl;

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

  uint32_t vEnableBit=99;
  tm.ReadSetting("EnableBit", vEnableBit);

  std::cout << "Enable bit: " << vEnableBit;

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

  std::cout << "Done" << std::endl;

  // Switch off trigger
  stat = tm.WriteSetting("ExtTriggerDirection", 0x0);

  //

  // Close all Sockets
  tm.CloseSockets();

  return 0;
}
