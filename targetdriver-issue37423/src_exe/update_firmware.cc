/*! \file */
/*!
 @file
 @brief Executable to update the firmware on a TM remotely
 */

#include <sys/socket.h>
#include <time.h>
#include <unistd.h>
#include <fstream>

#include "TargetDriver/DataPacket.h"
#include "TargetDriver/ModuleSimulator.h"
#include "TargetDriver/RegisterSettings.h"
#include "TargetDriver/TargetModule.h"
#include "TargetDriver/TesterBoard.h"
#include "TargetDriver/Waveform.h"
#include "TargetDriver/utils.h"

using namespace std;
using namespace CTA::TargetDriver;

int print_status(int flag) {
  std::cout << "---------------------" << std::endl;
  std::cout << " CONFIG FLASH STATUS " << std::endl;
  std::cout << "---------------------" << std::endl;
  std::cout << " Started           " << ((flag >> 6) & 1) << std::endl;
  std::cout << " Ready_BusyB       " << ((flag >> 14) & 1) << std::endl;
  std::cout << " Done              " << ((flag >> 13) & 1) << std::endl;
  std::cout << "---------------------" << std::endl;
  std::cout << " InitializeOK      " << ((flag >> 5) & 1) << std::endl;
  std::cout << " CheckIdOK         " << ((flag >> 4) & 1) << std::endl;
  std::cout << " EraseOK           " << ((flag >> 2) & 1) << std::endl;
  std::cout << " EraseSwitchWordOK " << ((flag >> 3) & 1) << std::endl;
  std::cout << " ProgramOK         " << ((flag >> 1) & 1) << std::endl;
  std::cout << " VerifyOK          " << ((flag >> 0) & 1) << std::endl;
  std::cout << "---------------------" << std::endl;
  std::cout << " Error             " << ((flag >> 12) & 1) << std::endl;
  std::cout << " ErrorCrc          " << ((flag >> 7) & 1) << std::endl;
  std::cout << " ErrorTimeOut      " << ((flag >> 8) & 1) << std::endl;
  std::cout << " ErrorProgram      " << ((flag >> 9) & 1) << std::endl;
  std::cout << " ErrorErase        " << ((flag >> 10) & 1) << std::endl;
  std::cout << " ErrorIdcode       " << ((flag >> 11) & 1) << std::endl;
  std::cout << "---------------------" << std::endl;

  return 0;
}

uint32_t shuffle_byte(uint32_t inbyte) {
  uint32_t outbyte = ((inbyte >> 24) & 0xFF) + (((inbyte >> 16) & 0xFF) << 8) +
                     (((inbyte >> 8) & 0xFF) << 16) + (((inbyte & 0xFF) << 24));
  return outbyte;
}

int main(int argc, char* argv[]) {
  timeval start, end;
  gettimeofday(&start, 0);
  if(argc < 4 ){
    std::cout<<"Usage: "<<argv[0]<<" FILENAME MY_IP TM_IP [CONF_FPGA] [CONF_ASIC] [CONF_TRIG_ASIC]"<< std::endl<< std::endl;
    std::cout<<"All arguments positional"<<std::endl<<std::endl;

    std::cout<<"   FILENAME       firmware file"<<std::endl;
    std::cout<<"   MY_IP          host ip"<<std::endl;
    std::cout<<"   TM_IP          Target module ip"<<std::endl;
    std::cout<<"   CONF_FPGA      FPGA definitions file (default: TC_M_FPGA_Firmware0xC0000008.de)"<<std::endl;
    std::cout<<"   CONF_ASIC      ASIC definitions file (default: TC_ASIC.def)"<<std::endl;
    std::cout<<"   CONF_TRIG_ASIC TRIG ASIC definitions file (default: T5TEA_ASIC.def)"<<std::endl;
    return 0;
  }

  std::string filename = argv[1];
  std::string my_ip = argv[2];//"192.168.15.1";
  std::string tm_ip = argv[3];//"192.168.15.173";
  std::string configPathFPGA =
      get_default_config_dir()+
      "/TC_M_FPGA_Firmware0xC0000008.def";
  if(argc>4)
    configPathFPGA =
      get_default_config_dir()+argv[4];

  std::string configPathASIC =
      get_default_config_dir()+
      "/TC_ASIC.def";
  if(argc>5)
    configPathASIC =
      get_default_config_dir()+argv[5];

  std::string configPathTriggerASIC =
      get_default_config_dir()+
      "/T5TEA_ASIC.def";
  if(argc>6)
    configPathTriggerASIC =
      get_default_config_dir()+argv[6];

  bool batchMode = false;
  if(argc>7)
    batchMode = (bool)argv[7];

  int stat;

  TargetModule tm(configPathFPGA, configPathASIC, configPathTriggerASIC);

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
  uint8_t ipaddr;
  tm.ReadModuleIP(ipaddr);
  std::cout << "Last Byte of IP: " << std::dec << int(ipaddr) << std::endl;

  if (batchMode) {
    std::cout << "Warning - batch mode - updating FW without user consent!" << std::endl;
  }
  else {
    std::cout << "Are you sure you want to update the firmware on " << tm_ip
	      << " ? (type 1 to proceed)" << std::endl;
    int i = 0;
    std::cin >> i;
    if (i != 1) exit(0);
  }

  uint32_t statusflag;
  //   tm.WriteSetting("Address_low",0x400000);
  //   tm.WriteSetting("Address_high",0x7B0000);
  tm.WriteSetting("ConfigFlashCheckID", 0);  // set to 1 only for debug
  tm.WriteSetting("ConfigFlashVerify", 0);   // set to 1 only for debug
  tm.ReadSetting("ConfigFlashStatus", statusflag);
  print_status(statusflag);
  // Enable the SPI clock
  tm.WriteSetting("ConfigFlashClkEnable", 1);

  // Reset the Flash (not the data, just addressing etc)
  tm.WriteSetting("ConfigFlashReset", 1);
  usleep(1000000);

  tm.WriteSetting("ConfigFlashReset", 0);

  std::cout << "--- ERASE MEMORY  ---" << std::endl;
  std::cout << "---------------------" << std::endl;
  int erasecnt = 0;
  int done = 0;
  while (!done) {
    tm.ReadSetting("ConfigFlashStatus", statusflag);
    done = (statusflag >> 2) & 1;
    usleep(1000000);
    erasecnt++;
  }
  std::cout << "---- ERASE DONE  ----" << std::endl;

  print_status(statusflag);
  usleep(100000);
  // one can read back if this 32 bits are already transferred before sending
  // the next ones. But transfer is done with ~30MHz, so takes 1µs, faster then
  // new packet arrives.
  std::cout << "-- PROGRAM MEMORY  --" << std::endl;
  uint32_t data;
  char* a;
  a = (char*)&data;
  int writecnt = 0;
  int wordcnt = 0;
  int wordprevious = 0;
  ifstream binfile(filename, ios::in | ios::binary);

  while (!binfile.eof()) {
    binfile.read(a, 4);
    if (wordcnt % 50000 == 0) {
      std::cout << std::hex << "Data 0x" << data << std::dec << " Wordnumber "
                << wordcnt << " of 966656" << std::endl;
      // print_status(statusflag);
    }
    //     if(wordcnt == 100)return 0;
    //     if(wordcnt<40){
    //      std::cout<<"Data "<<std::hex<<data<<" Shuffled "
    //      <<shuffle_byte(data) <<std::dec<<std::endl;
    //     }
    tm.WriteSetting("ConfigFlashData", shuffle_byte(data));
    done = 0;
    writecnt = 0;
    while (!done && wordcnt % 64 == 63) {  // after 64 words write buffer is
                                           // full and flash needs time to
                                           // complete writing
      tm.ReadSetting("ConfigFlashStatus", statusflag);
      done = (statusflag >> 14) & 1;
      //       if (!done){
      //          std::cout<<"Took longer for word "<<wordcnt<< " last
      //          "<<wordcnt-wordprevious<< " words ago "<<std::endl;
      //          wordprevious = wordcnt;
      //       }
      //       usleep(100000);
      //       done=1;
      writecnt++;
    }

    wordcnt++;
  }
  std::cout << std::hex << "Data 0x" << data << std::dec << " Wordnumber "
            << wordcnt << " of 966656" << std::endl;
  done = 0;
  writecnt = 0;
  while (!done) {
    tm.ReadSetting("ConfigFlashStatus", statusflag);
    std::cout << "Count " << writecnt << " Statusflag is " << std::hex
              << statusflag << std::dec << std::endl;
    done = (statusflag >> 13) & 1;
    writecnt++;
    usleep(1000000);
  }
  std::cout << "--- PROGRAM DONE  ---" << std::endl;
  std::cout << "---------------------" << std::endl;
  std::cout << "-  Ignore CRC error -" << std::endl;

  print_status(statusflag);
  tm.ReadSetting("CRC32", statusflag);
  std::cout << "CRC32 is " << std::hex << statusflag << std::dec << std::endl;
  std::cout << "---------------------" << std::endl;
  // tm.WriteSetting("ConfigFlashClkEnable",0);

  tm.CloseSockets();

  gettimeofday(&end, 0);
  int timediff = (end.tv_sec - start.tv_sec);
  std::cout << "Took " << timediff << "s to program." << std::endl;

  return 0;
}
