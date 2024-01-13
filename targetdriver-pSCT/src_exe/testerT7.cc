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

int main(int, char**) {
  // Specify your ip and ip of module
  std::string my_ip = "192.168.0.1";
  std::string tm_ip = "192.168.0.173";

  // Path to FPGA and ASIC def file
  std::string configPathFPGA =
      "/home/cta/TARGET/TargetDriver/branches/issue14135/config/"
      "T7_MSA_FPGA_Firmware0xA0000102.def";
  std::string configPathASIC =
      "/home/cta/TARGET/TargetDriver/branches/issue14135/config/T7_ASIC.def";
  int stat;

  // Establish communication with the real or simulated TM (also set FPGA
  // registers)
  // Happens on port 8201
  TargetModule tm(configPathFPGA.c_str(), configPathASIC.c_str());
  stat = tm.EstablishSlowControlLink(my_ip.c_str(), tm_ip.c_str());
  if (stat != TC_OK) {
    std::cout << "EstablishSlowControlLink() failed : "
              << tm.ReturnCodeToString(stat) << std::endl;
    exit(-1);
  }

  // Try to readout firmware
  uint32_t firmware;
  tm.ReadRegister(0x0, firmware);
  std::cout << "Firmware Version: " << std::hex << firmware << std::endl;

  // Initialise T7 Module with default settings
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

  // Set Vped, enable one channel for readout, enable hardsync mode and start
  // 120Hz trigger
  tm.WriteSetting("Vped_value", 2000);
  // enable only one channel in ASIC2 ///HARM not sure if this was intended
  tm.WriteSetting("EnableChannelsASIC2", 0x1);
  tm.WriteSetting("TACK_EnableTrigger", 0x10000);
  stat = tm.WriteSetting("ExtTriggerDirection", 0x1);

  // Akiras Hack needed for redirecting output to data port (8107)
  // will be fixed in later TM7 firmware versions
  TargetModule::DataPortPing(my_ip, tm_ip);

  usleep(300000);
  // Add DAQ listener on port 8107
  stat = tm.AddDAQListener(my_ip);
  if (stat != TC_OK) {
    std::cout << "AddDAQListener() failed : " << tm.ReturnCodeToString(stat)
              << std::endl;
    exit(-1);
  }

  for (int i = 0; i < 3; ++i) {
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
  // Turn off hardsync

  stat = tm.WriteSetting("ExtTriggerDirection", 0x0);
  // tm.WriteSetting("TACK_EnableTrigger", 0x0);
  // std::cout << "sync trigger switched off"<< std::endl;

  tm.CloseSockets();
  std::cout << "sockets closed" << std::endl;

  return 0;
}
