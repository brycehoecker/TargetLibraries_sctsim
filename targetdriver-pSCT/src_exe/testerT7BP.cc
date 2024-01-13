// Copyright (c) 2015 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Executable to test the TargetModule driver library
 */
#include <sys/socket.h>
#include <unistd.h>
#include <bitset>

#include "TargetDriver/DataPacket.h"
#include "TargetDriver/ModuleSimulator.h"
#include "TargetDriver/RegisterSettings.h"
#include "TargetDriver/TargetModule.h"
#include "TargetDriver/TesterBoard.h"
#include "TargetDriver/Waveform.h"

#define TM_NUM_COUNTERS 9

std::string kTMCounters[TM_NUM_COUNTERS] = {
    "CountGoodSyncTACKs",      "CountTACKsReceived",
    "CountSyncErrors",         "CountTACKRangeErrors",
    "CountTACKParityErrors",   "CountDataPackets",
    "CountDataPacketsEnabled", "CountTransmittedPackets",
    "CountProcessedEvents"};

bool ResetAllCounters(
    CTA::TargetDriver::TargetModule& tm) {  // NOLINT(runtime/references)
  for (int i = 0; i < TM_NUM_COUNTERS; ++i)
    tm.WriteSetting(kTMCounters[i].c_str(), 0);

  return true;
}

void PrintCounters(
    CTA::TargetDriver::TargetModule& tm) {  // NOLINT(runtime/references)
  for (int i = 0; i < TM_NUM_COUNTERS; ++i) {
    std::cout << kTMCounters[i] << "\t";
    uint32_t count = 0;
    int stat = tm.ReadSetting(kTMCounters[i], count);
    if (stat != TC_OK) count = 999999;
    std::cout << count << "\n";
  }
  std::cout << std::endl;
}

int main(int argc, char** argv) {
  //  RegisterSettings
  //  ts("./configFiles/TM5_FPGA_Firmware0xFEDA003C.def",
  //     "./configFiles/TM5_ASIC.def");
  //  std::cout << "Default settings: " << std::endl;
  //  ts.PrintAllSettings();
  //
  //  std::cout << "USER SETTINGS: " << std::endl;
  //  ts.ReadUserFPGAConfigFile("./configFiles/TM5_FPGA_UserXXX.config");
  //  ts.ReadUserASICConfigFile("./configFiles/TM5_ASIC_UserXXX.config");
  //  ts.PrintAllSettings();
  //
  //  return 0;

  bool simMode = false;
  std::string clientIP = "192.168.1.2";
  std::string moduleIP;

  if (argc == 1) {
    std::cout << "Running in simulation mode...\n " << std::endl;
    simMode = true;
  } else if (argc == 3 || argc == 4) {
    std::cout << "Running with target module" << std::endl;
  } else {
    std::cout << "Usage: ./tester <own-ip> <ip- Target Module> <ip -tester "
                 "board>(optional)\n"
              << " - To run in simulation mode don't provide any arguments \n"
              << " - To run with a single TM provide its ipaddress"
              << std::endl;
    return -1;
  }

  std::string testBoardIP = "192.168.1.173";
  if (simMode) {
    clientIP = "127.0.0.1";
    moduleIP = "127.0.0.1";
  } else {
    clientIP = argv[1];
    //    my_ip = "192.168.0.1";
    moduleIP = argv[2];
    if (argc > 3) {
      testBoardIP = argv[3];
    }
  }
  // setup a target simulator and listen in a seperate thread
  int stat;
  CTA::TargetDriver::ModuleSimulator* sim = 0;
  if (simMode) {
    sim = new CTA::TargetDriver::ModuleSimulator(moduleIP);
    //    sim->SetVerbose(true);
    sim->Start();
    std::cout << "Simulator thread launched" << std::endl;
    usleep(100000);
  }

  // Establish communication with the real or simulated TM

  CTA::TargetDriver::TargetModule tm(
      "/home/cta/CTA_software/TargetDriver/config/"
      "TM7_FPGA_Firmware0xB0000102.def",
      "config/TM7_ASIC.def", 0);
  stat = tm.EstablishSlowControlLink(clientIP, moduleIP);
  // PrintCounters(tm);
  if (stat != TC_OK) {
    std::cout << "EstablishSlowControlLink() failed : "
              << tm.ReturnCodeToString(stat) << std::endl;
    exit(-1);
  }

  if (!simMode) {
    CTA::TargetDriver::TargetModule::DataPortPing(clientIP, moduleIP);
  }

  usleep(100000);

  std::cout << "Getting TM Firmware Version" << std::endl;
  uint32_t fwv = 0;
  stat = tm.GetFirmwareVersion(fwv);

  usleep(100000);
  if (stat != TC_OK) {
    std::cout << "TM GetFirmwareVersion() failed : "
              << tm.ReturnCodeToString(stat) << std::endl;
    exit(-1);
  }
  std::cout << "FirmwareVersion: " << std::hex << fwv << std::dec << std::endl;

  // Try event data
  stat = tm.AddDAQListener(clientIP);
  if (stat != TC_OK) {
    std::cout << "AddDAQListener() failed : " << tm.ReturnCodeToString(stat)
              << std::endl;
    exit(-1);
  }

  if (simMode) {  // sim mode, generate some data and send it
    uint16_t samples = 128;
    uint16_t waves = 8;
    CTA::TargetDriver::DataPacket* p =
        new CTA::TargetDriver::DataPacket(waves, samples);
    // std::cout << "h1" << std::endl;
    p->FillHeader(waves, samples, 9, 10, 11, 99L, 2, 3, 4);
    uint16_t* data = 0;
    for (uint8_t i = 0; i < waves; ++i) {
      CTA::TargetDriver::Waveform* w = p->GetWaveform(i);
      w->PackWaveform(2, i, samples, false, data);
    }

    // Send the packet
    if ((stat = sim->SendDataPacket(p->GetData(), p->GetPacketSize())) !=
        TC_OK) {
      std::cout << "SendDataPacket() failed " << tm.ReturnCodeToString(stat)
                << std::endl;
      exit(-1);
    }

    // Send a 2nd packet
    p->FillHeader(waves, samples, 9, 10, 12, 9999L, 3, 4, 5);
    sim->SendDataPacket(p->GetData(), p->GetPacketSize());

  } else {  // if not simulaton mode -
    // First initialise the target module
    //    if ((stat = tm.Initialise()) != TC_OK) {
    // Initialise T7 Module with default settings
    if ((stat = tm.GoToPreSync()) != TC_OK) {
      std::cout << "TM initialisation failed: " << tm.ReturnCodeToString(stat)
                << std::endl;
      exit(-1);
    }
    uint32_t reg17;
    if ((stat = tm.ReadRegister(0x17, reg17)) != TC_OK) {
      std::cout << "Error reading register 17" << std::endl;
    } else {
      std::string binary = std::bitset<32>(reg17).to_string();
      std::cout << "register 17, before sync " << binary << std::endl;
    }
    // Tester board stuff
    CTA::TargetDriver::TesterBoard* tester = 0;
    tester = new CTA::TargetDriver::TesterBoard();
    std::cout << "--> Init Tester" << std::endl;
    stat = tester->Init(clientIP, testBoardIP);
    if (stat != TC_OK) {
      std::cout << " TesterBoard INIT FAILED "
                << " RICH - NO IT DIDN'T ! SYNC FAILED, NOT THE SAME THING - "
                   "NO it really failed - Jim"
                << std::endl;
    } else {
      std::cout << "--> Print Tester Status" << std::endl;
      tester->PrintStatus();
      std::cout << "--> Tester FW version = " << std::hex
                << tester->GetFirmwareVersion() << std::dec << std::endl;
      stat = tm.GoToReady();
      if (stat != TC_OK) {
        std::cout << "Go to ready failed: tm is undefined? " << tm.IsUndefined()
                  << std::endl;
      }
      uint32_t reg17;
      if ((stat = tm.ReadRegister(0x17, reg17)) != TC_OK) {
        std::cout << "Error reading register 17" << std::endl;
      } else {
        std::string binary = std::bitset<32>(reg17).to_string();
        std::cout << "register 17, after sync " << binary << std::endl;
      }
      tm.WriteSetting("Vped_value", 2000);
      tm.WriteSetting("EnableChannelsASIC0", 0xFFFF);
      tm.WriteSetting("EnableChannelsASIC1", 0xFFFF);
      tm.WriteSetting("EnableChannelsASIC2", 0xFFFF);
      tm.WriteSetting("EnableChannelsASIC3", 0xFFFF);

      std::cout << std::endl;
      PrintCounters(tm);
      std::cout << std::endl;

      std::cout << "Sending software trigger via tester" << std::endl;
      stat = tester->SendSoftwareTrigger();
      std::cout << "Statuts After tester->SendSoftwareTrigger(): " << stat
                << std::endl;
      usleep(100000);

      uint32_t regf;
      std::cout << "register 0xf " << std::hex << tm.ReadRegister(0xf, regf)
                << std::dec << std::endl;
      uint32_t reg10;
      std::cout << "register 0x10 " << std::hex << tm.ReadRegister(0x10, reg10)
                << std::dec << std::endl;

      std::cout << std::endl;
      PrintCounters(tm);
      std::cout << std::endl;

      //      stat = tester->SendSoftwareTrigger();
      //      std::cout << "Statuts After tester->SendSoftwareTrigger()
      //      (second): " << stat << std::endl;
    }
  }
  usleep(50000);

  // second time?
  // std::cout << "Sending software trigger via tester second time" <<
  // std::endl;
  // stat = tester->SendSoftwareTrigger();
  // std::cout << "Statuts After tester->SendSoftwareTrigger() (second): " <<
  // stat << std::endl;

  for (int i = 0; i < 10; ++i) {
    uint8_t d[10000];
    uint32_t bytes;
    std::cout << "Getting Data Packet " << std::endl;
    if ((stat = tm.GetDataPacket(&d, bytes, 10000)) != TC_OK) {
      std::cout << "GetDataPacket returned: " << tm.ReturnCodeToString(stat)
                << std::endl;
    } else {
      std::cout << "Received data packet with " << bytes << " bytes "
                << std::endl;
      CTA::TargetDriver::DataPacket prec;
      prec.Assign(d, static_cast<uint16_t>(bytes));
      prec.SummarisePacket();
    }
  }
  std::cout << "Done" << std::endl;

  //  std::cout << "\n Doing some read write test: " << std::endl;
  //  // a full register setting
  //  std::cout << "Writing in a partial register and reading back" <<
  //  std::endl; uint32_t readBack; std::cout <<
  //  tm.ReturnCodeToString(tm.ReadSetting("ExternalTrigIO", readBack))
  //            << std::endl;
  //  std::cout << "Read 1: " << std::hex << readBack << std::endl;
  //  uint32_t writeIn = 0x1;
  //  std::cout << tm.ReturnCodeToString(tm.WriteSetting("ExternalTrigIO",
  //  writeIn))
  //            << std::endl;
  //  std::cout << tm.ReturnCodeToString(tm.ReadSetting("ExternalTrigIO",
  //  readBack))
  //            << std::endl;
  //  std::cout << "Write 1: " << std::hex << writeIn << std::endl;
  //  std::cout << "Read 2: " << std::hex << readBack << std::endl;
  //
  //  std::cout << "\nWriting in a partial read only register and reading back"
  //            << std::endl;
  //  std::cout << tm.ReturnCodeToString(tm.ReadSetting("ExternalTrigIO",
  //  readBack))
  //            << std::endl;
  //  std::cout << "Read 1: " << std::hex << readBack << std::endl;
  //  writeIn = 0x1;
  //  std::cout << tm.ReturnCodeToString(tm.WriteSetting("Unused_0x4F_2",
  //  writeIn))
  //            << std::endl;
  //  std::cout << tm.ReturnCodeToString(tm.ReadSetting("Unused_0x4F_2",
  //  readBack))
  //            << std::endl;
  //  std::cout << "Write 1: " << std::hex << writeIn << std::endl;
  //  std::cout << "Read 2: " << std::hex << readBack << std::endl;
  //
  //  std::cout << "\nWriting another unused  partial register and reading back"
  //            << std::endl;
  //  std::cout << tm.ReturnCodeToString(tm.ReadSetting("Unused_Vped1",
  //  readBack))
  //            << std::endl;
  //  std::cout << "Read 1: " << std::hex << readBack << std::endl;
  //  writeIn = 0x1FF;
  //  std::cout << tm.ReturnCodeToString(tm.WriteSetting("Unused_Vped1",
  //  writeIn))
  //            << std::endl;
  //  std::cout << tm.ReturnCodeToString(tm.ReadSetting("Unused_Vped1",
  //  readBack))
  //            << std::endl;
  //  std::cout << "Write 1: " << std::hex << writeIn << std::endl;
  //  std::cout << "Read 2: " << std::hex << readBack << std::endl;
  //
  //  std::cout << "\nWriting another Vped2  partial register and reading back"
  //            << std::endl;
  //  std::cout << tm.ReturnCodeToString(tm.ReadSetting("ASIC2_Vped", readBack))
  //            << std::endl;
  //  std::cout << "Read 1: " << std::hex << readBack << std::endl;
  //  writeIn = 0x1FF;
  //  std::cout << tm.ReturnCodeToString(tm.WriteSetting("ASIC2_Vped", writeIn))
  //            << std::endl;
  //  std::cout << tm.ReturnCodeToString(tm.ReadSetting("ASIC2_Vped", readBack))
  //            << std::endl;
  //  std::cout << "Write 1: " << std::hex << writeIn << std::endl;
  //  std::cout << "Read 2: " << std::hex << readBack << std::endl;
  //
  //  std::cout << "\n Reading back some monitor values: " << std::endl;
  //  uint32_t isReady;
  //  float val;
  //
  //  tm.ReadSetting("Temperature1_Valid", isReady);
  //  tm.ReadSettingCalibrated("Temperature1", val);
  //  std::cout << "Temperature1: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //  tm.ReadSetting("Temperature0_Valid", isReady);
  //  tm.ReadSettingCalibrated("Temperature0", val);
  //  std::cout << "Temperature0: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //
  //  tm.ReadSetting("ASIC0_Current_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC0_Current", val);
  //  std::cout << "ASIC0_Current: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC1_Current_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC1_Current", val);
  //  std::cout << "ASIC1_Current: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC2_Current_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC2_Current", val);
  //  std::cout << "ASIC2_Current: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC3_Current_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC3_Current", val);
  //  std::cout << "ASIC3_Current: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //
  //  tm.ReadSetting("ASIC0_Voltage_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC0_Voltage", val);
  //  std::cout << "ASIC0_Voltage: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC1_Voltage_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC1_Voltage", val);
  //  std::cout << "ASIC1_Voltage: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC2_Voltage_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC2_Voltage", val);
  //  std::cout << "ASIC2_Voltage: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC3_Voltage_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC3_Voltage", val);
  //  std::cout << "ASIC3_Voltage: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //
  //  tm.ReadSetting("ASIC0_Vped_Meas_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC0_Vped_Meas", val);
  //  std::cout << "ASIC0_Vped_Meas: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC1_Vped_Meas_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC1_Vped_Meas", val);
  //  std::cout << "ASIC1_Vped_Meas: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC2_Vped_Meas_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC2_Vped_Meas", val);
  //  std::cout << "ASIC2_Vped_Meas: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC3_Vped_Meas_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC3_Vped_Meas", val);
  //  std::cout << "ASIC3_Vped_Meas: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //
  //  tm.ReadSetting("ASIC0_Vdly_Meas_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC0_Vdly_Meas", val);
  //  std::cout << "ASIC0_Vdly_Meas: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC1_Vdly_Meas_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC1_Vdly_Meas", val);
  //  std::cout << "ASIC1_Vdly_Meas: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC2_Vdly_Meas_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC2_Vdly_Meas", val);
  //  std::cout << "ASIC2_Vdly_Meas: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC3_Vdly_Meas_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC3_Vdly_Meas", val);
  //  std::cout << "ASIC3_Vdly_Meas: " << val << "\t Ready bit: " << isReady
  //            << std::endl;
  //
  //  tm.ReadSetting("ASIC0_SumDischargeIsel_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC0_SumDischargeIsel", val);
  //  std::cout << "ASIC0_SumDischargeIsel: " << val << "\t Ready bit: " <<
  //  isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC1_SumDischargeIsel_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC1_SumDischargeIsel", val);
  //  std::cout << "ASIC1_SumDischargeIsel: " << val << "\t Ready bit: " <<
  //  isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC2_SumDischargeIsel_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC2_SumDischargeIsel", val);
  //  std::cout << "ASIC2_SumDischargeIsel: " << val << "\t Ready bit: " <<
  //  isReady
  //            << std::endl;
  //  tm.ReadSetting("ASIC3_SumDischargeIsel_Valid", isReady);
  //  tm.ReadSettingCalibrated("ASIC3_SumDischargeIsel", val);
  //  std::cout << "ASIC3_SumDischargeIsel: " << val << "\t Ready bit: " <<
  //  isReady
  //            << std::endl;
  //  std::cout << std::endl;
  //
  //  uint32_t ival;
  //
  //  std::cout << "ASIC VPED read back: " << std::endl;
  //  tm.ReadSetting("ASIC0_Vped", ival);
  //  std::cout << "ASIC0_Vped" << ival << std::endl;
  //
  //  tm.ReadSettingCalibrated("ASIC0_Vped", val);
  //  std::cout << "ASIC0_Vped (calibrated) " << val << std::endl;
  std::cout << std::endl;
  PrintCounters(tm);
  std::cout << std::endl;
  std::cout << "Resetting the counters..." << std::endl;
  ResetAllCounters(tm);
  std::cout << std::endl;
  PrintCounters(tm);

  return 0;
}
