// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include "TargetDriver/TargetModule.h"

#include <stdlib.h>
#include <cmath>
#include <iostream>
#include <sstream>

namespace CTA {
namespace TargetDriver {

TargetModule::TargetModule(uint16_t pModuleId)
    : UDPClient(TM_MAX_ATTEMPTS, TM_RESPONSE_TIME_OUT, TM_DAQ_TIME_OUT),
      fTargetSettings("", ""),
      fTargetSettingsDefault("", ""),
      fModuleId(pModuleId),
      fClockPhase(0),
      fState(TM_STATE_UNDEFINED),
      fModuleType(kNonTM),
      fClientIP(""),
      fModuleIP("") {}

TargetModule::TargetModule(const std::string& pFPGADef,
                           const std::string& pASICDef, uint16_t pModuleId)
    : UDPClient(TM_MAX_ATTEMPTS, TM_RESPONSE_TIME_OUT, TM_DAQ_TIME_OUT),
      fTargetSettings(pFPGADef, pASICDef),
      fTargetSettingsDefault(pFPGADef, pASICDef),
      fModuleId(pModuleId),
      fClockPhase(0),
      fState(TM_STATE_UNDEFINED),
      fModuleType(kNonTM),
      fClientIP(""),
      fModuleIP("") {
  // Set Target module type
  if (fTargetSettings.fType == "TM_5") {
    fModuleType = kT5Module;
  } else if (fTargetSettings.fType == "TM_7") {
    fModuleType = kT7Module;
  } else if (fTargetSettings.fType == "TM_7_BP") {
    fModuleType = kT7ModuleBP;
  } else if (fTargetSettings.fType == "TC_EVAL") {
    fModuleType = kTCEval;
  } else if (fTargetSettings.fType == "TCT5TEA_EVAL") {
    fModuleType = kTCT5TEAEval;
  } else if (fTargetSettings.fType == "TM_C") {
    fModuleType = kTCModule;
  } else if (fTargetSettings.fType == "TM_C_BP") {
    fModuleType = kTCModuleBP;
  } else {
    std::cerr
        << "Unknown target module type defined in firmware definition file:"
        << std::endl;
    std::cerr << pFPGADef << std::endl;
    exit(-1);
  }
}

void TargetModule::SetIPAddresses(const std::string& pClientIP,
                                  const std::string& pModuleIP) {
  fClientIP = pClientIP;
  fModuleIP = pModuleIP;
}

TargetModule::TargetModule(const std::string& pFPGADef,
                           const std::string& pASICDef,
                           const std::string& pTriggerASICDef,
                           uint16_t pModuleId)
    : fTargetSettings(pFPGADef, pASICDef, pTriggerASICDef),
      fTargetSettingsDefault(pFPGADef, pASICDef, pTriggerASICDef),
      fModuleId(pModuleId),
      fClockPhase(0),
      fState(TM_STATE_UNDEFINED),
      fModuleType(kNonTM),
      fClientIP(""),
      fModuleIP("") {
  // Set Target module type
  if (fTargetSettings.fType == "TM_5") {
    fModuleType = kT5Module;
  } else if (fTargetSettings.fType == "TM_7") {
    fModuleType = kT7Module;
  } else if (fTargetSettings.fType == "TM_7_BP") {
    fModuleType = kT7ModuleBP;
  } else if (fTargetSettings.fType == "TC_EVAL") {
    fModuleType = kTCEval;
  } else if (fTargetSettings.fType == "TCT5TEA_EVAL") {
    fModuleType = kTCT5TEAEval;
  } else if (fTargetSettings.fType == "TM_C") {
    fModuleType = kTCModule;
  } else if (fTargetSettings.fType == "TM_C_BP") {
    fModuleType = kTCModuleBP;
  } else {
    std::cerr
        << "Unknown target module type defined in firmware definition file:"
        << std::endl;
    std::cerr << pFPGADef << std::endl;
    exit(-1);
  }
}

int TargetModule::AddDAQListener(const std::string& my_ip) {
  return AddDataListener(my_ip, TM_DAQ_PORT, TM_SOCK_BUF_SIZE_DAQ);
}

int TargetModule::ReconnectToServer(const std::string& pMyIP,
                                    uint16_t pMySourcePort,
                                    const std::string& pServerIP,
                                    uint16_t pServerPort,
                                    int32_t pSocketBufferSize) {
  int stat = ConnectToServer(pMyIP, pMySourcePort, pServerIP, pServerPort,
                             pSocketBufferSize);
  if (stat != TC_OK) {
    std::cerr << "Could not Reconnect to server " << std::endl;
    return stat;
  }
  stat = FillRegisterMapFromFPGA();
  if (stat != TC_OK) {
    std::cerr << "Fill RegisterMapFromFPGA failed, in "
                 "TargetModule::ReconnectToServer "
              << std::endl;
    return stat;
  }

  fTargetSettings.UpdateFPGASettingMapFromRegisterMap();
  stat = FillRegisterMapFromFPGA();
  if (stat != TC_OK) {
    std::cerr << "Fill UpdateFPGASettingMapFromRegisterMap failed, in "
                 "TargetModule::ReconnectToServer "
              << std::endl;
    return stat;
  }
  return stat;
}

int TargetModule::GetPrimaryBoardID(uint64_t& pbid) {
  uint32_t lsw, msw;
  ReadRegister(0x02, lsw);
  int stat = ReadRegister(0x03, msw);
  pbid = ((msw & 0xFFFFFF) << 24) + (lsw >> 8);

  std::cout << "GetPrimID: " << std::hex << " " << msw << " " << lsw << " "
            << ((msw & 0xFFFFFF) << 24) << " " << (lsw >> 8) << std::endl;

  return stat;
}

int TargetModule::GoToSafe() {
  // HARM DOESN'T STOP SAMPLING, SHOULD IT?
  int stat = TC_OK;

  fState = TM_STATE_UNRESPONSIVE;

  // Writing default FPGA register values into the Target Module

  for (auto itF = fTargetSettingsDefault.fSettingMapFPGA.begin();
       itF != fTargetSettingsDefault.fSettingMapFPGA.end(); ++itF) {
    if (itF->first != "PhaseOfCommsClock") {
      //      if(!itF->second.isReadOnly) {
      if (itF->second.access == eRW) {
        // HACK:
        stat = WriteSetting(itF->first, itF->second.value);

        // WriteSetting(itF->first,itF->second.value); before fixing non-sticky
        // bits
      }
    }
    if (stat != TC_OK) return stat;
  }

  // Setting some T5 specific values,  if (fModuleType == kT5Module) {
  if (fModuleType == kT5Module) {
    if ((stat = WriteSetting("EventPortNumber", TM_DAQ_PORT)) != TC_OK)
      return stat;
    if ((stat = WriteSetting("ModuleIndex", fModuleId)) != TC_OK) return stat;
  }

  // setting the t7 specific values
  // clang-format off
  if (fModuleType == kT7Module || fModuleType == kT7ModuleBP ||
      fModuleType == kTCEval   || fModuleType == kTCModuleBP ||
      fModuleType == kTCModule /* || fModuleType == kTCT5TEAEval*/) {
    // clang-format on
    if (fTargetSettings.fSettingMapFPGA.find("SetDataPort") !=
        fTargetSettings.fSettingMapFPGA.end()) {
      if ((stat = WriteSetting("SetDataPort", TM_DAQ_PORT)) != TC_OK) {
        return stat;
      }
    }
    // if ((stat = WriteSetting("DetectorID", fModuleId)) != TC_OK) return stat;
  }
  // disable the HV to super pixels by default
  if (fModuleType == kTCModuleBP || fModuleType == kTCModule) {
    if ((stat = DisableHVAll()) != TC_OK) return stat;
  }

  if (fVerbose) {
    std::cout << "TargetModule::GoToSafe() succeeded" << std::endl;
  }
  fState = TM_STATE_SAFE;

  return TC_OK;
}

int TargetModule::GoToPreSync() {
  int stat = TC_OK;
  if (fState <= TM_STATE_UNDEFINED) {
    std::cout << "TargetModule::GoToPreSync() called with TM in "
                 "undefined/uncontactable state "
              << fState << std::endl;
    if ((stat = GoToSafe()) != TC_OK) return stat;
  }

  // Slight change of logic - do not call initialise if we are already in the
  // presync or ready state
  if (fState < TM_STATE_PRESYNC) {
    if (fVerbose) {
      std::cout << "TargetModule::GoToPreSync() called with TM in state "
                << fState << " - initialising " << std::endl;
    }
    stat = Initialise();
    if (stat != TC_OK) {
      std::cout << "TargetModule::GoToPreSync() - Initialise failed "
                << std::endl;
      fState = TM_STATE_UNRESPONSIVE;
      return stat;
    }
  }

  stat = DisableDLLFeedBack();
  if (stat != TC_OK) {
    std::cout << "Failed to disable DLL feed back" << std::endl;
    fState = TM_STATE_UNRESPONSIVE;
    return stat;
  }

  StopSampling();

  fState = TM_STATE_PRESYNC;

  return TC_OK;
}

int TargetModule::GoToReady() {
  if (fVerbose) {
    std::cout << "TM:GoToReady" << std::endl;
  }
  if (fState != TM_STATE_PRESYNC)
    return TC_ERR_USER_ERROR;  // only for BP modules

  int stat;
  // clang-format off
  if (fModuleType == kT7Module   || fModuleType == kT7ModuleBP ||
      fModuleType == kTCModuleBP || fModuleType == kTCModule) {
    // clang-format on
    stat = EnableDLLFeedback();  // LT: needs to enabled after Sync
    if (stat != TC_OK) {
      fState = TM_STATE_UNRESPONSIVE;
      return stat;
    }
  }

  // check enable bit
  uint32_t ebit = 99;
  if ((stat = ReadSetting("EnableBit", ebit)) != TC_OK) {
    std::cout << "Failed to read enablebit - setting TM state to UNRESPONSIVE"
              << std::endl;
    fState = TM_STATE_UNRESPONSIVE;
    return stat;
  }

  if (ebit == 0) {
    fState = TM_STATE_PRESYNC;
    return TC_UNEXPECTED_RESPONSE;
  }

  if (ebit == 1) {
    fState = TM_STATE_READY;

    if (fVerbose) {
      std::cout << "TM:GoToReady - TM is in READY state" << std::endl;
      std::cout << "-----------------------------------" << std::endl;
    }
    return TC_OK;
  }

  return TC_UNEXPECTED_RESPONSE;
}

// For backward compatibility
int TargetModule::EstablishSlowControlLink(const std::string& pClientIP,
                                           const std::string& pModuleIP) {
  fClientIP = pClientIP;
  fModuleIP = pModuleIP;

  return Connect();
}

int TargetModule::Connect() {
  fState = TM_STATE_UNRESPONSIVE;

  if (fClientIP.size() < 7 || (fModuleIP.size() < 7)) {
    std::cout << "TargetModule::Connect() - ERROR - bad IPs: client "
              << fClientIP << " module " << fModuleIP << std::endl;
    return TC_ERR_USER_ERROR;
  }

  CloseSockets();

  int stat;
  if (fModuleType == kT5Module) {
    stat = ConnectToServer(fClientIP, TM_SOURCE_PORT + fModuleId, fModuleIP,
                           TM_DEST_PORT, TM_SOCK_BUF_SIZE_SC);
  } else if (fModuleType == kT7Module || fModuleType == kT7ModuleBP ||
             fModuleType == kTCEval || fModuleType == kTCT5TEAEval ||
             fModuleType == kTCModule || fModuleType == kTCModuleBP) {
    uint16_t slowPort = TM_SOURCE_PORT + fModuleId;  // default option
    if (fTargetSettings.fSettingMapFPGA.find("SetSlowControlPort") !=
        fTargetSettings.fSettingMapFPGA.end()) {
      if (fTargetSettings.fSettingMapFPGA["SetSlowControlPort"].value != 0) {
        slowPort = uint16_t(
            fTargetSettings.fSettingMapFPGA["SetSlowControlPort"].value);
      }
    }
    stat = ConnectToServer(fClientIP, slowPort, fModuleIP, TM_DEST_PORT,
                           TM_SOCK_BUF_SIZE_SC);
  } else {
    stat = TC_ERR_CONF_FAILURE;
  }

  if (stat != TC_OK) return stat;

  DataPortPing();

  if (fVerbose) {
    std::cout
        << "TargetModule::Connect - connected to server - now set comms phase: "
        << std::endl;
  }
  fClockPhase = -1;
  if (fModuleType == kT5Module || fModuleType == kT7ModuleBP ||
      fModuleType == kTCModuleBP) {
    if (fVerbose) {
      std::cout << "Trying first comm's phase, ignore send attempts errors"
                << std::endl;
    }
    // WriteSetting("PhaseOfCommsClock", 0);
    if ((stat = WriteSetting("PhaseOfCommsClock", 0)) == TC_OK) {
      fClockPhase = 0;
    } else {
      // WriteSetting("PhaseOfCommsClock", 1);
      if (fVerbose) std::cout << "Trying second comms phase..." << std::endl;
      if ((stat = WriteSetting("PhaseOfCommsClock", 1)) == TC_OK) {
        fClockPhase = 1;
      }
    }
    if (fClockPhase < 0) {
      std::cout
          << "TargetModule -- Both comms phases failed - abandoning Connect()"
          << std::endl;
      return stat;
    }
    if (fVerbose)
      std::cout << "TargetModule::Connect -- comms phase set successfully to "
                << fClockPhase << std::endl;
  } else {
    if (fVerbose)
      std::cout << "TargetModule::Connect successfully." << std::endl;
  }

  if (fClockPhase)
    if (fVerbose)
      std::cout << "Clock phase is OK - Ignore the previous attemps errors"
                << std::endl;

  uint32_t fw_version = 0;
  if ((stat = GetFirmwareVersion(fw_version)) != TC_OK) return stat;

  if (fw_version != fTargetSettings.fFPGAFirmwareVersion) {
    std::cout << "ERROR: Firmware read: " << std::hex << fw_version
              << "\t but in *def file: " << fTargetSettings.fFPGAFirmwareVersion
              << std::endl;
    return TC_UNEXPECTED_RESPONSE;
  }

  fState = TM_STATE_UNDEFINED;

  return GoToSafe();
}

bool TargetModule::Exists(std::string ipaddress, std::string myip) {
  CloseSockets();

  int stat = ConnectToServer(myip, TM_SPECIAL_PORT, ipaddress, TM_DEST_PORT,
                             TM_SOCK_BUF_SIZE_SC);

  if (stat != TC_OK) {
    std::cout << "TM:Exists() - problem with ConnectToServer" << std::endl;
    return false;
  }

  int ClockPhase = -1;
  if ((stat = WriteSetting("PhaseOfCommsClock", 0)) == TC_OK) {
    ClockPhase = 0;
  } else {
    if ((stat = WriteSetting("PhaseOfCommsClock", 1)) == TC_OK) {
      ClockPhase = 1;
    }
  }

  CloseSockets();

  return (ClockPhase > -1);
}

void TargetModule::PackControlPacket(uint8_t* bytes, uint32_t address,
                                     uint32_t data, bool iswrite) {
  memset(bytes, 0, TM_CONTROLPACKET_SIZE);

  bytes[6] = TM_CONTROLPACKET_SIZE;

  if (iswrite) {
    bytes[4] |= 0x40;
  } else {
    bytes[4] &= 0x3F;
  }
  bytes[5] = (address >> 16) & 0xFF;
  bytes[6] = (address >> 8) & 0xFF;
  bytes[7] = (address >> 0) & 0xFF;
  bytes[8] = (data >> 24) & 0xFF;
  bytes[9] = (data >> 16) & 0xFF;
  bytes[10] = (data >> 8) & 0xFF;
  bytes[11] = (data >> 0) & 0xFF;
}

int TargetModule::UnpackControlPacket(const uint8_t* bytes, uint32_t& addr,
                                      uint32_t& data, bool& iswrite) {
  int stat = CheckResponse(bytes);

  if (stat != TC_OK) {
    //    if (fVerbose)
    std::cout << "TM unpack packet Check Response failed" << std::endl;
    iswrite = false;
    data = 0;
    addr = 0;
    return stat;
  }

  iswrite = ((bytes[4] & 0x40) != 0);

  // clang-format off
  data = ((uint32_t)(bytes[ 8]) << 24) | ((uint32_t)(bytes[ 9]) << 16) |
         ((uint32_t)(bytes[10]) <<  8) | ((uint32_t)(bytes[11]) <<  0);

  addr = ((uint32_t)(bytes[ 5]) << 16) | ((uint32_t)(bytes[ 6]) <<  8) |
         ((uint32_t)(bytes[ 7]) <<  0);
  // clang-format on

  // if (fVerbose) {
  //   std::cout << "Unpack Control Packet " << iswrite << " " << data << " " <<
  //   addr << std::endl;
  // }
  return TC_OK;
}

int TargetModule::CheckResponse(const uint8_t* packet)  //, uint32_t length) {
{  //  if ((length != TM_CONTROLPACKET_SIZE) || ((packet[4] & 0x80) != 0)) {
  if ((packet[4] & 0x80) != 0) {
    //    std::cout << "CR - len: " << (int)length << " p4: " << (int)packet[4]
    //    << std::endl;
    return TC_ERR_BAD_PACKET;
  }
  return TC_OK;
}

int TargetModule::RegisterOperation(uint32_t address, uint32_t& data,
                                    bool iswrite, bool onlySend) {
  PackControlPacket(fBuffer, address, data, iswrite);
  ssize_t len;
  int stat;

  // std::cout << "RegisterOperation " << address << " " << data << " " <<
  // iswrite << std::endl;
  // in the case we don't expect a response
  if (onlySend) {
    DiscardPacketsInTheSocketBuffer();  // flush in case message/response has
                                        // got out of sync
    if ((stat = Send(fBuffer, TM_CONTROLPACKET_SIZE)) != TC_OK) {
      std::cerr << "Send failed in: UDPClient::SendAndReceive, error code: "
                << stat << ": " << ReturnCodeToString(stat) << std::endl;
    }
    return stat;
  }

  if ((stat = SendAndReceive(fBuffer, TM_CONTROLPACKET_SIZE, fBuffer, len,
                             TM_CONTROLPACKET_SIZE + 1)) != TC_OK) {
    fState = TM_STATE_UNRESPONSIVE;
    return stat;
  }
  uint32_t resp_addr;
  bool resp_write;
  UnpackControlPacket(fBuffer, resp_addr, data, resp_write);

  //  std::cout << " GOT: (data)" << std::hex <<data << "from address "  <<
  //  std::hex << address << std::endl;

  if (resp_addr != address) {
    std::cerr << "ERROR TargetModule::RegisterOperation(): Receiving data from "
                 "address: 0x"
              << std::hex << resp_addr << ", while writing to address: 0x"
              << address << std::endl;
    data = 0;
    return TC_ERR_BAD_PACKET;
  }
  return TC_OK;
}

int TargetModule::WriteRegisterAndCheck(uint32_t address, uint32_t data) {
  int stat;
  if ((stat = WriteRegister(address, data)) != TC_OK) return stat;

  uint32_t data_read;
  if ((stat = ReadRegister(address, data_read)) != TC_OK) return stat;
  if (data_read != data) {
    std::cout << "WriteRegisterAndCheck: Wrote: " << data
              << "\t But read back: " << data_read << std::endl;
    return TC_UNEXPECTED_RESPONSE;
  }

  return TC_OK;
}

// HARM  MOVE TO GOTOPRESYNC
void TargetModule::StopSampling() {
  int state = fState;
  WriteSetting("SoftwareReset", 0xBECEDACE);
  state = fState;  // to avoid that this puts us in undefined state
}

int TargetModule::WriteSetting(const std::string& name, uint32_t val) {
  int stat;
  if ((stat = fTargetSettings.ModifyFPGASetting(name, val)) != TC_OK)
    return stat;
  uint32_t address;
  fTargetSettings.GetFPGASettingRegisterAddress(name, address);
  uint32_t fullReg;
  fTargetSettings.GetFPGARegisterValue(address, fullReg);

  // exception for software reset, since no answer is expected
  if (name == "SoftwareReset") {
    stat = RegisterOperation(address, fullReg, true, true);
    //    WriteRegister(address, fullReg);
    fTargetSettings.ModifyFPGASetting(name, 0);
    return stat;
  }

  //  if (!fTargetSettings.fSettingMapFPGA[name].isReadOnly) {
  if (fTargetSettings.fSettingMapFPGA[name].access == eRW ||
      fTargetSettings.fSettingMapFPGA[name].access == eRW_NS) {
    stat = WriteRegister(address, fullReg);

    // std::cout << "called WriteRegister for setting " << name << " val: " <<
    // fullReg << std::endl;

  } else if (fTargetSettings.fSettingMapFPGA[name].access == eR) {
    std::cerr << "Cannot write setting <" << name << ">, it is read-only"
              << std::endl;
    std::cerr << "Fix your code! (or check that FPGA-def is correct)"
              << std::endl;
    stat = TC_ERR_USER_ERROR;
  } else if (fTargetSettings.fSettingMapFPGA[name].access == eW) {
    WriteRegister(address, fullReg);
    fTargetSettings.ModifyFPGASetting(name, 0);
    return TC_OK;
  }

  if (stat != TC_OK) return stat;

  if (fTargetSettings.fSettingMapFPGA[name].access == eRW) {
    uint32_t readBack;
    stat = ReadSetting(name, readBack);
    if (fVerbose) std::cout << "read back setting - stat: " << stat << "\n";
    if (readBack != val) {
      std::cerr
          << "ERROR: WriteRegister, while ReadSetting (for check) in setting "
          << name << "\t" << val << ", but received back: " << readBack
          << std::endl;
      return TC_UNEXPECTED_RESPONSE;  // debug
    }
  }
  return stat;
}

int TargetModule::ReadSetting(const std::string& name, uint32_t& val) {
  uint32_t address;
  fTargetSettings.GetFPGASettingRegisterAddress(name, address);
  uint32_t valFullBuffer;
  int stat;
  if ((stat = ReadRegister(address, valFullBuffer)) != TC_OK) return stat;
  fTargetSettings.GetRegisterPartially(
      valFullBuffer, fTargetSettings.fSettingMapFPGA[name], val);

  // std::cout << "ReadSetting " << name << " val: " << val << std::endl;

  return stat;
}

int TargetModule::WriteSettingFromConfig(const std::string& name) {
  uint32_t address;
  fTargetSettings.GetFPGASettingRegisterAddress(name, address);
  uint32_t val;
  fTargetSettings.GetFPGARegisterValue(address, val);
  return WriteRegisterAndCheck(address, val);
  // TODO(Harm): error handling - would use TC_OK and TC_ERR_CONF_FAILURE
}

int TargetModule::WriteRegisterFromConfig(uint32_t address) {
  uint32_t val;
  fTargetSettings.GetFPGARegisterValue(address, val);
  //  return WriteRegisterAndCheck(address,val);
  return WriteRegister(address, val);
}

int TargetModule::WriteTARGETRegister(bool enableAsic0, bool enableAsic1,
                                      bool enableAsic2, bool enableAsic3,
                                      bool readback, bool latchIsRequired,
                                      uint8_t address, uint16_t value,
                                      bool isTriggerASIC) {
  uint32_t data = 0;
  uint16_t ASICWriteRegister = 0;
  uint16_t ASICReadBackRegister = 0;

  if (fVerbose) {
    std::cout << "TM:WTR add=" << (int)address << " val=" << (int)value
              << " istrigasic=" << (int)isTriggerASIC
              << " toASICS:" << (int)enableAsic0 << (int)enableAsic1
              << (int)enableAsic2 << (int)enableAsic3 << std::endl;
  }
  // Distinguish between TM5 and TM7 due to different ASIC Read/Write register
  // addresses
  // and different sizes of ASIC addresses
  if (fModuleType == kT5Module) {
    if (address > 0x3F || value > 0xFFF) {
      return TC_ERR_USER_ERROR;
    }
    data |= ((uint32_t)(enableAsic0) << 20) | ((uint32_t)(enableAsic1) << 21) |
            ((uint32_t)(enableAsic2) << 22) | ((uint32_t)(enableAsic3) << 23);
    data |= ((uint32_t)(readback) << 19) |
            ((uint32_t)(latchIsRequired ? 0x0 : 0x1) << 18);
    data |= (uint32_t)(address) << 12;
    data |= (uint32_t)(value);
    ASICWriteRegister = 0x50;
    ASICReadBackRegister = 0x51;
  } else if (fModuleType == kT7Module || fModuleType == kT7ModuleBP) {
    if (address > 0x4F || value > 0xFFF) {
      return TC_ERR_USER_ERROR;
    }
    data |= ((uint32_t)(enableAsic0) << 21) | ((uint32_t)(enableAsic1) << 22) |
            ((uint32_t)(enableAsic2) << 23) | ((uint32_t)(enableAsic3) << 24);
    data |= ((uint32_t)(readback) << 20) |
            ((uint32_t)(latchIsRequired ? 0x0 : 0x1) << 19);
    data |= (uint32_t)(address) << 12;
    data |= (uint32_t)(value);
    ASICWriteRegister = 0x60;
    ASICReadBackRegister = 0x61;
  } else if (fModuleType == kTCEval) {
    if (address > 0x5C || value > 0xFFF) {
      return TC_ERR_USER_ERROR;
    }

    data |= ((uint32_t)(enableAsic0) << 21) | ((uint32_t)(enableAsic1) << 22) |
            ((uint32_t)(enableAsic2) << 23) | ((uint32_t)(enableAsic3) << 24);
    data |= ((uint32_t)(readback) << 20) |
            ((uint32_t)(latchIsRequired ? 0x0 : 0x1) << 19);
    data |= (uint32_t)(address) << 12;
    data |= (uint32_t)(value);
    ASICWriteRegister = 0x60;
    ASICReadBackRegister = 0x61;
  } else if (fModuleType == kTCT5TEAEval || fModuleType == kTCModule ||
             fModuleType == kTCModuleBP) {
    if (!isTriggerASIC) {
      if (address > 0x5C || value > 0xFFF) {
        return TC_ERR_USER_ERROR;
      }
    } else {
      if (address > 0x38 || value > 0xFFF) {
        return TC_ERR_USER_ERROR;
      }
    }

    data |= ((uint32_t)(enableAsic0) << 21) | ((uint32_t)(enableAsic1) << 22) |
            ((uint32_t)(enableAsic2) << 23) | ((uint32_t)(enableAsic3) << 24);
    data |= ((uint32_t)(readback) << 20) |
            ((uint32_t)(latchIsRequired ? 0x0 : 0x1) << 19);
    data |= (uint32_t)(address) << 12;
    data |= (uint32_t)(value);
    if (!isTriggerASIC) {
      ASICWriteRegister = 0x60;
      ASICReadBackRegister = 0x61;
      // Adrian: need so set T5TEA register to 0 (especially the four bits which
      // select active ASIC) that FPGA logic can handle SCLK and PCLK
      WriteRegister(0x63, 0x0);
    } else {
      ASICWriteRegister = 0x63;
      ASICReadBackRegister = 0x64;
      // Adrian: need so set TC register to 0 (especially the four bits which
      // select active ASIC) that FPGA logic can handle SCLK and PCLK
      WriteRegister(0x60, 0x0);
    }

  } else {
    std::cout << "TargetType fTMType not specified, cannot write ASIC Registers"
              << std::endl;
  }
  int stat;
  if ((stat = WriteRegister(ASICWriteRegister, data)) != TC_OK) {
    return stat;
  }

  // Readback of last written value not working, reads back value written
  // before. Seems
  // to be an error in the firmware
  if (readback) {
    usleep(500);  // TODO(Harm): needs optimisation

    if (enableAsic0 || enableAsic1) {
      uint32_t check;
      stat = ReadRegister(ASICReadBackRegister, check);
      if (stat != TC_OK) {
        return stat;
      }
      if (enableAsic0 && ((check & 0xFFF) != value)) {
        return TC_UNEXPECTED_RESPONSE;
      }
      if (enableAsic1 && (((check >> 16) & 0xFFF) != value)) {
        return TC_UNEXPECTED_RESPONSE;
      }
    }
    if (enableAsic2 || enableAsic3) {
      uint32_t check;
      stat = ReadRegister(ASICReadBackRegister + 1, check);
      if (stat != TC_OK) {
        return stat;
      }
      if (enableAsic2 && ((check & 0xFFF) != value)) {
        return TC_UNEXPECTED_RESPONSE;
      }
      if (enableAsic3 && (((check >> 16) & 0xFFF) != value)) {
        return TC_UNEXPECTED_RESPONSE;
      }
    }
  }

  return TC_OK;
}

int TargetModule::WriteASICSetting(const std::string& name, uint8_t asic,
                                   uint16_t val, bool individualASIC,
                                   bool isTriggerASIC) {
  uint8_t address;
  fTargetSettings.GetASICSettingRegisterAddress(name, address, isTriggerASIC);

  if (fVerbose) {
    std::cout << "TM:WriteASICSetting: " << name << " asic " << (int)asic
              << " val " << (int)val << std::endl;
  }
  // update config map
  if (individualASIC) {
    // modify the register in the map
    fTargetSettings.ModifyASICSetting(name, asic, val, isTriggerASIC);
    // get back the modified register from the map, i.e. update val
    fTargetSettings.GetASICRegisterValue(name, asic, val, isTriggerASIC);
    //     if (address == 0x5 )
    //       std::cout << "Writing 0x" << std::hex << val << " into 0x5,
    //       isTriggerASIC: " << isTriggerASIC << std::endl;

    switch (asic) {
      case 0:
        WriteTARGETRegister(true, false, false, false, true, true, address, val,
                            isTriggerASIC);
        break;
      case 1:
        WriteTARGETRegister(false, true, false, false, true, true, address, val,
                            isTriggerASIC);
        break;
      case 2:
        WriteTARGETRegister(false, false, true, false, true, true, address, val,
                            isTriggerASIC);
        break;
      case 3:
        WriteTARGETRegister(false, false, false, true, true, true, address, val,
                            isTriggerASIC);
        break;
      default:
        std::cout << "ERROR: asic number must be 0, 1, 2 or 3" << std::endl;
        break;
    }
  } else {
    for (asic = 0; asic < 4; ++asic) {
      fTargetSettings.ModifyASICSetting(name, asic, val, isTriggerASIC);
      fTargetSettings.GetASICRegisterValue(name, asic, val, isTriggerASIC);
    }
    WriteTARGETRegister(true, true, address, val, isTriggerASIC);
  }

  // TODO(Harm) - error handling

  return TC_OK;
}

int TargetModule::WriteASICSettingFromConfig(const std::string& name,
                                             uint8_t asic, bool individualASIC,
                                             bool isTriggerASIC) {
  uint8_t address;
  fTargetSettings.GetASICSettingRegisterAddress(name, address, isTriggerASIC);
  uint16_t val = 0;

  if (!individualASIC) {
    // TODO(Harm): Don't use the same variable for this loop.
    for (asic = 0; asic < 4; ++asic) {
      fTargetSettings.GetASICRegisterValue(name, asic, val, isTriggerASIC);
      switch (asic) {
        case 0:
          WriteTARGETRegister(true, false, false, false, true, true, address,
                              val, isTriggerASIC);
          break;
        case 1:
          WriteTARGETRegister(false, true, false, false, true, true, address,
                              val, isTriggerASIC);
          break;
        case 2:
          WriteTARGETRegister(false, false, true, false, true, true, address,
                              val, isTriggerASIC);
          break;
        case 3:
          WriteTARGETRegister(false, false, false, true, true, true, address,
                              val, isTriggerASIC);
          break;
        default:
          std::cout << "ERROR: ASIC number must be 0, 1, 2 or 3" << std::endl;
          break;
      }
    }

  } else {
    fTargetSettings.GetASICRegisterValue(name, asic, val, isTriggerASIC);
    switch (asic) {
      case 0:
        WriteTARGETRegister(true, false, false, false, true, true, address, val,
                            isTriggerASIC);
        break;
      case 1:
        WriteTARGETRegister(false, true, false, false, true, true, address, val,
                            isTriggerASIC);
        break;
      case 2:
        WriteTARGETRegister(false, false, true, false, true, true, address, val,
                            isTriggerASIC);
        break;
      case 3:
        WriteTARGETRegister(false, false, false, true, true, true, address, val,
                            isTriggerASIC);
        break;
      default:
        std::cout << "ERROR: asic number must be 0, 1, 2 or 3" << std::endl;
        break;
    }
  }
  // TODO(Harm) Return or propagate error code
  return TC_OK;
}

int TargetModule::WriteASICRegisterFromConfig(uint8_t address, uint8_t asic,
                                              bool individualASIC,
                                              bool isTriggerASIC) {
  uint16_t val = 0;

  if (!individualASIC) {
    for (uint8_t asicLoop = 0; asicLoop < 4; ++asicLoop) {
      if (!isTriggerASIC) {
        val = fTargetSettings.fRegisterMapASIC[address].val[asicLoop];

      } else {
        val = fTargetSettings.fRegisterMapTriggerASIC[address].val[asicLoop];
      }

      switch (asicLoop) {
        case 0:
          WriteTARGETRegister(true, false, false, false, true, true, address,
                              val, isTriggerASIC);
          break;
        case 1:
          WriteTARGETRegister(false, true, false, false, true, true, address,
                              val, isTriggerASIC);
          break;
        case 2:
          WriteTARGETRegister(false, false, true, false, true, true, address,
                              val, isTriggerASIC);
          break;
        case 3:
          WriteTARGETRegister(false, false, false, true, true, true, address,
                              val, isTriggerASIC);
          break;
        default:
          std::cout << "TargetModule ERROR: asic number must be 0, 1, 2 or 3"
                    << std::endl;
          break;
      }
    }
  } else {
    if (!isTriggerASIC) {
      val = fTargetSettings.fRegisterMapASIC[address].val[asic];
    } else {
      val = fTargetSettings.fRegisterMapTriggerASIC[address].val[asic];
    }

    switch (asic) {
      case 0:
        WriteTARGETRegister(true, false, false, false, true, true, address, val,
                            isTriggerASIC);
        break;
      case 1:
        WriteTARGETRegister(false, true, false, false, true, true, address, val,
                            isTriggerASIC);
        break;
      case 2:
        WriteTARGETRegister(false, false, true, false, true, true, address, val,
                            isTriggerASIC);
        break;
      case 3:
        WriteTARGETRegister(false, false, false, true, true, true, address, val,
                            isTriggerASIC);
        break;
      default:
        std::cout << "TargetModule ERROR: asic number must be 0, 1, 2 or 3"
                  << std::endl;
        break;
    }
  }

  return TC_OK;
}

int TargetModule::WriteSettingCalibrated(const std::string& name, float val) {
  float multiplier = fTargetSettings.fSettingMapFPGA[name].multiplier;
  float offset = fTargetSettings.fSettingMapFPGA[name].offset;
  uint32_t intVal;
  float eps = 1e-9f;
  if (fabs(multiplier) < eps && fabs(offset) > eps) {
    intVal = static_cast<uint32_t>(val - offset);
  } else if (fabs(multiplier) < eps && fabs(offset) < eps) {
    // std::cout << "For setting (WriteSettingCalibrated)" << name << std::endl;
    // std::cout << "Calibration constants are 0 in definition file" <<
    // std::endl;
    return TC_ERR_CONF_FAILURE;
  } else {
    intVal = static_cast<uint32_t>((val - offset) / multiplier);
  }
  return WriteSetting(name, intVal);
}

int TargetModule::ReadSettingCalibrated(const std::string& name, float& val) {
  float multiplier = fTargetSettings.fSettingMapFPGA[name].multiplier;
  float offset = fTargetSettings.fSettingMapFPGA[name].offset;
  uint32_t intVal;
  int stat;
  if ((stat = ReadSetting(name, intVal)) != TC_OK) {
    return stat;
  }

  float eps = 1e-9f;
  if (fabs(multiplier) < eps && fabs(offset) < eps) {
    // std::cout << "For setting (ReadSettingCalibrated) " << name << std::endl;
    // std::cout << ", calibration constants are 0 in definition file"
    // << std::endl;
    val = intVal;
    return TC_ERR_CONF_FAILURE;
  } else if (fabs(multiplier) < eps && fabs(offset) > eps) {
    val = intVal + offset;
  } else {
    val = intVal * multiplier + offset;
  }

  return stat;
}

int TargetModule::WriteSettingASICCalibrated(const std::string& name,
                                             uint8_t asic, float val,
                                             bool individualASIC,
                                             bool isTriggerASIC) {
  float multiplier;
  float offset;
  if (individualASIC) {
    // TODO(Harm): Check if asic > 3
    if (!isTriggerASIC) {
      multiplier =
          fTargetSettings.fSettingMapASIC[name].settingASIC[asic].multiplier;
      offset = fTargetSettings.fSettingMapASIC[name].settingASIC[asic].offset;
    } else {
      multiplier = fTargetSettings.fSettingMapTriggerASIC[name]
                       .settingASIC[asic]
                       .multiplier;
      offset =
          fTargetSettings.fSettingMapTriggerASIC[name].settingASIC[asic].offset;
    }
  } else {
    if (!isTriggerASIC) {
      multiplier =
          fTargetSettings.fSettingMapASIC[name].settingASIC[0].multiplier;
      offset = fTargetSettings.fSettingMapASIC[name].settingASIC[0].offset;
    } else {
      multiplier = fTargetSettings.fSettingMapTriggerASIC[name]
                       .settingASIC[0]
                       .multiplier;
      offset =
          fTargetSettings.fSettingMapTriggerASIC[name].settingASIC[0].offset;
    }
  }

  uint16_t iVal;
  if (multiplier == 0) {
    iVal = static_cast<uint16_t>(val - offset);
  } else if (multiplier == 0 && offset == 0) {
    std::cout << "TargetModule Calibration constants are 0 in definition file"
              << std::endl;
    return TC_ERR_CONF_FAILURE;
  } else {
    iVal = static_cast<uint16_t>((val - offset) / multiplier);
  }

  return WriteASICSetting(name, asic, iVal, individualASIC, isTriggerASIC);
}

int TargetModule::PowerUpASIC(uint8_t asic, bool individualASIC) {
  uint32_t power_sleep = 3 * 1000;  // 3 ms
  uint32_t bias_sleep = 1 * 1000;   // 1 ms

  int stat = TC_OK;

  // Need to ensure that SetPLKWidth and SetSINSettlingTime stuff is dealt with
  // in FPGA auto loop

  for (int a = 0; a < 4; ++a) {
    if (!individualASIC || (a == asic)) {
      std::stringstream setting;
      setting << "PowerUpASIC" << a;
      // setting += a;
      // Set power to this ASIC
      if ((stat = WriteSetting(setting.str(), 1)) != TC_OK) {
        return stat;
      }
      usleep(power_sleep);
      // Turn up the ITbias DAC voltage
      std::stringstream setting2;
      setting2 << "ITbias_" << a;
      // setting += a;
      if ((stat = WriteSettingFromConfig(setting.str())) != TC_OK) {
        return stat;
      }

      // JAH - Could do more here - would be good to talk to Gary or Leonid
      // usleep(bias_sleep);
      // stat = WriteSettingFromConfig("DBbias"); // bring up the DBbias voltage

      if (a < 3 && !individualASIC) {
        usleep(bias_sleep);
      }
    }
  }

  // Remaining ASIC settings should be applied in auto loop

  return TC_OK;
}

int TargetModule::CheckRegisters() {
  // Check that all registers are written and consistent with the *def files

  for (auto citF = fTargetSettings.fRegisterMapFPGA.begin();
       citF != fTargetSettings.fRegisterMapFPGA.end(); ++citF) {
    uint32_t val = 0;
    int stat = ReadRegister(citF->first, val);
    if (stat != TC_OK) {
      return stat;
    }

    for (auto citS = fTargetSettings.fSettingMapFPGA.begin();
         citS != fTargetSettings.fSettingMapFPGA.end(); ++citS) {
      if (citF->first == citS->second.regAddr) {
        bool check = fTargetSettings.CheckRegisterPartially(citF->second.val,
                                                            citS->second);
        if (!check) {
          std::cout << "TargetModule Checking of Setting failed: "
                    << citS->first << std::endl;
          std::cout << "Setting is: " << std::endl;
          fTargetSettings.PrintFPGASetting(citS->first);
          std::cout << "Register is: " << std::hex << citF->second.val
                    << std::endl;
          return TC_UNEXPECTED_RESPONSE;
        }
      }
    }
  }
  return TC_OK;
}

int TargetModule::Initialise() {
  // Definitions file is read in already. User could have called read config
  // before

  int stat = CheckRegisters();

  if (fVerbose) {
    std::cout << "TargetModule - Initialise " << stat << std::endl;
  }
  if (stat != TC_OK) {
    return stat;
  }

  // Mock syncing with Backplane for evaluation boards and stand-alone modules l
  if (fModuleType == kT7Module || fModuleType == kTCEval ||
      fModuleType == kTCT5TEAEval || fModuleType == kTCModule) {
    // This whole block is a sync, therefore order of register writing is
    // needed.
    if ((stat = WriteRegister(0x33, 0x00100000)) != TC_OK) {  // Mocking the
                                                              // sync
      return stat;
    }
    if ((stat = WriteRegister(0x33, 0x80100000)) != TC_OK) {
      return stat;
    }
  }

  if ((stat = PowerUpASIC()) != TC_OK) {
    return stat;
  }

  // Write the ASIC registers
  for (auto citA = fTargetSettings.fRegisterMapASIC.begin();
       citA != fTargetSettings.fRegisterMapASIC.end(); ++citA) {
    int stat = WriteASICRegisterFromConfig(citA->first);
    if (stat != TC_OK) {
      return stat;
    }
  }

  // write trigger asic registers
  if (fModuleType == kTCT5TEAEval || fModuleType == kTCModule ||
      fModuleType == kTCModuleBP) {
    for (auto citA = fTargetSettings.fRegisterMapTriggerASIC.begin();
         citA != fTargetSettings.fRegisterMapTriggerASIC.end(); ++citA) {
      int stat = WriteTriggerASICRegisterFromConfig(citA->first);
      if (stat != TC_OK) {
        return stat;
      }
    }
  }

  // TODO: Why are we doing this only for Target 5??
  if (fModuleType == kT5Module) {
    // clang-format off
    if ((stat = WriteSetting("EnableChannelsASIC0", 0xFFFF)) != TC_OK) return stat;
    if ((stat = WriteSetting("EnableChannelsASIC1", 0xFFFF)) != TC_OK) return stat;
    if ((stat = WriteSetting("EnableChannelsASIC2", 0xFFFF)) != TC_OK) return stat;
    if ((stat = WriteSetting("EnableChannelsASIC3", 0xFFFF)) != TC_OK) return stat;
    // clang-format on
  }

  // enable some Target 7, and later, specific stuff (needs documentation)
  // clang-format off
  if (fModuleType == kT7Module || fModuleType == kT7ModuleBP  ||
      fModuleType == kTCEval   || fModuleType == kTCT5TEAEval ||
      fModuleType == kTCModule || fModuleType == kTCModuleBP) {
    // usleep(100000);
    // LT: this sleep does not seem necessary, remove as part of issue 14135?
    if ((stat = WriteASICSetting("SSPinLE_Delay", 0, 0x2e)) != TC_OK) return stat;
    if ((stat = WriteASICSetting("SSPinTE_Delay", 0, 0x3d)) != TC_OK) return stat;

    // New Timing Parameters for TC (Get rid of Prepulses) (by Manuel and David)
    if (fModuleType == kTCT5TEAEval || fModuleType == kTCEval ||
        fModuleType == kTCModule    || fModuleType == kTCModuleBP) {
      if ((stat = WriteASICSetting("WR_ADDR_Incr1LE_Delay", 0, 55)) != TC_OK) return stat;
      if ((stat = WriteASICSetting("WR_ADDR_Incr1TE_Delay", 0,  6)) != TC_OK) return stat;
      if ((stat = WriteASICSetting("WR_STRB1LE_Delay",      0, 25)) != TC_OK) return stat;
      if ((stat = WriteASICSetting("WR_STRB1TE_Delay", 0, 25 + 10)) != TC_OK) return stat;
      if ((stat = WriteASICSetting("WR_ADDR_Incr2LE_Delay", 0, 55)) != TC_OK) return stat;
      if ((stat = WriteASICSetting("WR_ADDR_Incr2TE_Delay", 0,  6)) != TC_OK) return stat;
      if ((stat = WriteASICSetting("WR_STRB2LE_Delay",      0, 61)) != TC_OK) return stat;
      if ((stat = WriteASICSetting("WR_STRB2TE_Delay",      0,  7)) != TC_OK) return stat;
    } else {  // Timing Parameters for T7
      if ((stat = WriteASICSetting("WR_ADDR_Incr1LE_Delay", 0, 0x3f)) != TC_OK) return stat;
      if ((stat = WriteASICSetting("WR_ADDR_Incr1TE_Delay", 0,   14)) != TC_OK) return stat;
      if ((stat = WriteASICSetting("WR_STRB1LE_Delay",      0, 0x23)) != TC_OK) return stat;
      if ((stat = WriteASICSetting("WR_STRB1TE_Delay",      0, 0x2d)) != TC_OK) return stat;
      if ((stat = WriteASICSetting("WR_ADDR_Incr2LE_Delay", 0, 0x25)) != TC_OK) return stat;
      if ((stat = WriteASICSetting("WR_ADDR_Incr2TE_Delay", 0, 0x34)) != TC_OK) return stat;
      if ((stat = WriteASICSetting("WR_STRB2LE_Delay",      0,    2)) != TC_OK) return stat;
      if ((stat = WriteASICSetting("WR_STRB2TE_Delay",      0,   12)) != TC_OK) return stat;
    }

    if ((stat = WriteASICSetting("VtrimT",         0, 0x4d8)) != TC_OK) return stat;
    if ((stat = WriteASICSetting("SSToutFB_Delay", 0, 0x03a)) != TC_OK) return stat;
    // clang-format on
    // Need to warm up to avoid bimodal noise distribution
    // issue 14135, reduce from 5 second to 10 ms, at 1 ms observed timebase
    // instabilities (LT)
    usleep(50000); // Someone seems to have increased to 50 ms after LT comment - would be good to know why
  }
  return TC_OK;
}

// HARM Add disable DLL feedback loop...
int TargetModule::EnableDLLFeedback() {
  int stat;
  // clang-format off
  if (fModuleType == kT7Module || fModuleType == kT7ModuleBP  ||
      fModuleType == kTCEval   || fModuleType == kTCT5TEAEval ||
      fModuleType == kTCModule || fModuleType == kTCModuleBP) {
    // start time base for standalone modules and eval boards
    if (fModuleType == kT7Module    || fModuleType == kTCEval ||
        fModuleType == kTCT5TEAEval || fModuleType == kTCModule) {
      if ((stat = WriteRegister(0x33,     0x00180000)) != TC_OK) return stat;
      if ((stat = WriteRegister(0x33,     0x80180000)) != TC_OK) return stat;
      if ((stat = WriteRegister(0x33,     0x00100000)) != TC_OK) return stat;
      if ((stat = WriteSetting("Start_TimeBase", 0x1)) != TC_OK) return stat;
    }
    // clang-format on
    // issue 14135, reduce from 5 second to 1 ms, seems to be sufficient for
    // proper timebase init, don't care to reduce more (LT)
    usleep(1000);
    // Enable DLL feedback, sequence is very important, this is needed to set
    // the sampling frequency
    // clang-format off
    if ((stat = WriteASICSetting("Vqbuff",  0, 0x426)) != TC_OK) return stat;
    if ((stat = WriteASICSetting("Qbias",   0, 0x5DC)) != TC_OK) return stat;
    if ((stat = WriteASICSetting("VadjN",   0, 0x834)) != TC_OK) return stat;
    if ((stat = WriteASICSetting("VadjN",   0, 0x8bb)) != TC_OK) return stat;  // VadjN hardcoded,
    if ((stat = WriteASICSetting("VANbuff", 0, 0x000)) != TC_OK) return stat;
    // clang-format on
    // go back to normal trigger mode for standalone modules and eval boards
    if (fModuleType == kT7Module || fModuleType == kTCEval ||
        fModuleType == kTCT5TEAEval || fModuleType == kTCModule) {
      if ((stat = WriteRegister(0x33, 0x0)) != TC_OK) return stat;
    }
  } else {
    return TC_ERR_USER_ERROR;
  }
  return stat;
}

int TargetModule::DisableDLLFeedBack() {
  int stat;
  // clang-format off
  if (fModuleType == kT7Module || fModuleType == kT7ModuleBP  ||
      fModuleType == kTCEval   || fModuleType == kTCT5TEAEval ||
      fModuleType == kTCModule || fModuleType == kTCModuleBP) {
    if ((stat = WriteASICSetting("VANbuff", 0, 0x426)) != TC_OK) return stat;
    if ((stat = WriteASICSetting("Qbias",   0, 0x000)) != TC_OK) return stat;
    if ((stat = WriteASICSetting("Vqbuff",  0, 0x000)) != TC_OK) return stat;
    if ((stat = WriteASICSetting("VadjN",   0, 0x8BB)) != TC_OK) return stat;
    // clang-format on
    // start time base for standalone modules and eval boards
    usleep(1000);
  } else {
    return TC_ERR_USER_ERROR;
  }
  return stat;
}

int TargetModule::FillRegisterMapFromFPGA() {
  for (auto cit = fTargetSettings.fRegisterMapFPGA.begin();
       cit != fTargetSettings.fRegisterMapFPGA.end(); ++cit) {
    uint32_t value;
    int stat = ReadRegister(cit->first, value);
    if (stat != TC_OK) {
      std::cerr << "Error while reading register 0x" << std::hex << cit->first
                << " in function TargetModule::FillRegisterMapFromFPGA()"
                << std::endl;
    }

    fTargetSettings.fRegisterMapFPGA[cit->first].val = value;
  }
  return TC_OK;
}

void TargetModule::QueryAndPrintAllRegisters(
    std::ostream& stream) {  // NOLINT(runtime/references)

  for (auto cit = fTargetSettings.fRegisterMapFPGA.begin();
       cit != fTargetSettings.fRegisterMapFPGA.end(); ++cit) {
    uint32_t value;
    int stat = ReadRegister(cit->first, value);
    stream << cit->first << "\t" << value << "\t" << stat;
  }
}

void TargetModule::DataPortPing() { DataPortPing(fClientIP, fModuleIP); }

void TargetModule::DataPortPing(const std::string& pClientIP,
                                const std::string& pModuleIP) {
  // Avoid firewall problem by contacting TM on data port prior to any data
  // sending
  UDPClient dummy(2, 5, 5);
  dummy.ConnectToServer(pClientIP, TM_DAQ_PORT, pModuleIP, TM_DEST_PORT);
  char resp[100];
  char message = '1';
  ssize_t resplen = 0;
  dummy.SendAndReceive(&message, 1, resp, resplen, 100);
}

void TargetModule::DeleteDAQListeners() {
  for (unsigned int i = 0; i < fDAQPollList.size(); ++i) {
    close(fDAQPollList[i].fd);
  }

  fDAQPollList.clear();
}

//
// Read the HV input to the module
int TargetModule::ReadHVCurrentInput(float& val /*A*/) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "TargetModule ERROR: This function is only implemented for "
                 "kTCModule and kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }

  int ret;

  if ((ret = WriteSetting("I2CAddr_Power", 0b1101111)) != TC_OK) return ret;

  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Power", 1)) != TC_OK) return ret;

  if ((ret = WriteSetting("I2CRegAddr_Power", 0)) != TC_OK) return ret;

  // Starts the operation, non sticky
  //    std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  uint32_t answer;
  if ((ret = ReadSetting("I2CReadData_Power", answer)) != TC_OK) return ret;

  uint16_t tempVal = ((answer & 0xFF) << 4) + ((answer >> 12) & 0xF);
  val = tempVal * 20e-6;

  return TC_OK;
}

int TargetModule::ReadHVVoltageInput(float& val /*V*/) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "TargetModule ERROR: This function is only implemented for "
                 "kTCModule and kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }

  int ret;

  if ((ret = WriteSetting("I2CAddr_Power", 0b1101111)) != TC_OK) return ret;

  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Power", 1)) != TC_OK) return ret;

  if ((ret = WriteSetting("I2CRegAddr_Power", 2)) != TC_OK) return ret;

  // Starts the operation, non sticky
  //    std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  uint32_t answer;
  if ((ret = ReadSetting("I2CReadData_Power", answer)) != TC_OK) return ret;

  uint16_t tempVal = ((answer & 0xFF) << 4) + ((answer >> 12) & 0xF);

  val = tempVal * 0.025;

  return TC_OK;
}

int TargetModule::GetTempI2CPower(float& val /*Celsius*/) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "TargetModule ERROR: This function is only implemented for "
                 "kTCModule and kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }

  int ret;

  if ((ret = WriteSetting("I2CAddr_Power", 0b1001000)) != TC_OK) return ret;

  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Power", 1)) != TC_OK) return ret;

  if ((ret = WriteSetting("I2CRegAddr_Power", 0)) != TC_OK) return ret;

  // Starts the operation, non sticky
  //    std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  uint32_t answer;
  if ((ret = ReadSetting("I2CReadData_Power", answer)) != TC_OK) return ret;

  uint16_t tempVal = ((answer & 0x7F) << 1) + ((answer >> 15) & 0x1);
  val = tempVal * 0.5;
  int sign = (answer >> 7) & 1;
  if (sign) val *= -1;
  return TC_OK;
}

int TargetModule::GetTempI2CAux(float& val /*Celsius*/) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "TargetModule ERROR: This function is only implemented for "
                 "kTCModule and kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }

  int ret;

  // no need to set device address, it is set in firmware

  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Aux", 1)) != TC_OK) return ret;

  if ((ret = WriteSetting("I2CRegAddr_Aux", 0)) != TC_OK) return ret;

  // Starts the operation, non sticky
  //    std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Aux", 1)) != TC_OK) return ret;

  uint32_t answer;
  if ((ret = ReadSetting("I2CReadData_Aux", answer)) != TC_OK) return ret;

  uint16_t tempVal = (answer >> 8) + ((answer & 0xFF) << 8);
  val = (tempVal >> 3) * 0.03125;
  if ((tempVal >> 15) & 0x1) val *= -1;
  return TC_OK;
}

int TargetModule::GetTempI2CPrimary(float& val /*Celsius*/) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "TargetModule ERROR: This function is only implemented for "
                 "kTCModule and kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }

  int ret;

  // no need to set device address, it is set in firmware

  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Primary", 1)) != TC_OK) return ret;

  if ((ret = WriteSetting("I2CRegAddr_Primary", 0)) != TC_OK) return ret;

  // Starts the operation, non sticky
  //    std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Primary", 1)) != TC_OK) return ret;

  uint32_t answer;
  if ((ret = ReadSetting("I2CReadData_Primary", answer)) != TC_OK) return ret;

  uint16_t tempVal = (answer >> 8) + ((answer & 0xFF) << 8);
  val = (tempVal >> 3) * 0.03125;
  if ((tempVal >> 15) & 0x1) val *= -1;

  return TC_OK;
}

//
int TargetModule::GetTempSIPM(float& val) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "ERROR: This function is only implemented for kTCModule and "
                 "kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }
  int ret;
  uint32_t answer;
  uint32_t answer2;
  if ((ret = ReadSetting("SlowADCEnable_Power", answer)) != TC_OK) return ret;
  if (answer != 1) {
    if ((ret = WriteSetting("SlowADCEnable_Power", 1)) != TC_OK) return ret;
    std::cout << "TargetModule::GetTempSIPM - sleep after enabling slow adc power" << std::endl;
    sleep(1);
  }
  if ((ret = ReadSetting("SlowResult27_Power", answer2)) != TC_OK) return ret;
  if (answer2 < 0x8000)
    answer2 += 0x8000;
  else
    answer2 = answer2 & 0x7FFF;
  val = (answer2 * 0.03815 * .2) - 273.15;
  val = (int)(val * 100.) / 100.0;
  return TC_OK;
}

int TargetModule::ReadPowerBoardID(uint64_t& val) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "TargetModule ERROR: This function is only implemented for "
                 "kTCModule and kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }

  int ret;

  if ((ret = WriteSetting("I2CAddr_Power", 0b1010000)) != TC_OK) return ret;

  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Power", 1)) != TC_OK) return ret;

  uint32_t answer[4];
  for (int i = 0; i < 4; i++) {
    if ((ret = WriteSetting("I2CRegAddr_Power", 2 * i)) != TC_OK) return ret;
    // Starts the operation, non sticky
    //      std::cout << "expected error, non sticky bit" << std::endl;
    if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;
    if ((ret = ReadSetting("I2CReadData_Power", answer[i])) != TC_OK)
      return ret;
  }
  val = ((answer[0]) & 0xFF00) + ((answer[0] & 0xFF));
  val += (((answer[1]) & 0xFF00) + ((answer[1] & 0xFF))) << 16;
  val += (((answer[2]) & 0xFF00) + ((answer[2] & 0xFF))) << 32;
  val += (((answer[3]) & 0xFF00) + ((answer[3] & 0xFF))) << 48;

  return TC_OK;
}

//
// two bytes for 16 super pixel channels
// Enabling / Disabling  HV
// private?
int TargetModule::ReadHVEnableBytes(uint8_t& byte0, uint8_t& byte1) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "TargetModule ERROR: This function is only implemented for "
                 "kTCModule and kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }

  int ret;
  if ((ret = WriteSetting("I2CAddr_Power", 0b0100001)) != TC_OK) return ret;

  // read back the value we just have written
  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Power", 1)) != TC_OK) return ret;

  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  uint32_t answer;
  if ((ret = ReadSetting("I2CReadData_Power", answer)) != TC_OK) return ret;

  byte1 = (answer & 0xFF);
  byte0 = (answer >> 8 & 0xFF);

  return TC_OK;
}

//
//
//
//
//

int TargetModule::IsHVEnabled(uint8_t superPixel, bool& enabled) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "TargetModule ERROR: This function is only implemented for "
                 "kTCModule and kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }
  int ret;

  int enableBit = SuperPixelIdToHVEneableBit(superPixel);
  if (enableBit < 0) return TC_UNEXPECTED_RESPONSE;
  uint8_t byte0, byte1;
  if ((ret = ReadHVEnableBytes(byte0, byte1)) != TC_OK) return ret;

  if (enableBit < 8) {
    uint8_t specBit = 1 << enableBit;
    enabled = (specBit & byte0);
  } else {
    enableBit -= 8;
    uint8_t specBit = 1 << enableBit;
    enabled = (specBit & byte1);
  }
  return TC_OK;
}

int TargetModule::WhichHVEnabled(std::vector<bool>& enabled) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "TargetModule ERROR: This function is only implemented for "
                 "kTCModule and kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }
  enabled.clear();
  enabled.resize(16, false);
  int ret;
  // read current bytes
  uint8_t byte0, byte1;
  if ((ret = ReadHVEnableBytes(byte0, byte1)) != TC_OK) return ret;

  for (uint8_t spId = 0; spId < 16; spId++) {
    int enableBit = SuperPixelIdToHVEneableBit(spId);
    if (enableBit < 0) return TC_UNEXPECTED_RESPONSE;
    if (enableBit < 8) {
      uint8_t specBit = 1 << enableBit;
      if (specBit & byte0) {  // check if bit is up
        enabled[spId] = true;
      }
    } else {
      enableBit -= 8;
      uint8_t specBit = 1 << enableBit;
      if (specBit & byte1) {  // check if bit is up
        enabled[spId] = true;
      }
    }
  }

  return TC_OK;
}  // all superpixels

int TargetModule::DisableHVSuperPixel(uint8_t superPixel) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "TargetModuleERROR: This function is only implemented for "
                 "kTCModule and kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }

  int ret;
  int enableBit = SuperPixelIdToHVEneableBit(superPixel);
  if (enableBit < 0) return TC_UNEXPECTED_RESPONSE;

  // read current bytes
  uint8_t byte0, byte1;

  if ((ret = ReadHVEnableBytes(byte0, byte1)) != TC_OK) return ret;

  // modify bytes to disable bit
  if (enableBit < 8) {
    uint8_t specBit = 1 << enableBit;
    if (specBit & byte0) {  // check if bit is up
      byte0 = ~specBit & byte0;
    }
  } else {
    enableBit -= 8;
    uint8_t specBit = 1 << enableBit;
    if (specBit & byte1) {  // check if bit is up
      byte1 = ~specBit & byte1;
    }
  }

  // 0b0100001 is I2C bus of the I/0 expander (TI PCA9555)
  if ((ret = WriteSetting("I2CAddr_Power", 0b0100001)) != TC_OK) return ret;

  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Power", 0)) != TC_OK) return ret;

  // not sure why this block is needed..
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x6)) != TC_OK) return ret;

  if ((ret = WriteSetting("I2CWriteData_Power", 0)) != TC_OK) return ret;

  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  if ((ret = WriteSetting("I2CRegAddr_Power", 0x7)) != TC_OK) return ret;
  if ((ret = WriteSetting("I2CWriteData_Power", 0)) != TC_OK) return ret;

  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  // Writing enable byte 0
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x2)) != TC_OK) return ret;
  if ((ret = WriteSetting("I2CWriteData_Power", byte0)) != TC_OK) return ret;
  //    std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;
  // writing enable byte 1
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x3)) != TC_OK) return ret;
  if ((ret = WriteSetting("I2CWriteData_Power", byte1)) != TC_OK) return ret;

  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;
  usleep(1e5);
  // reading back bytes for checking
  uint8_t check0, check1;

  if ((ret = ReadHVEnableBytes(check0, check1)) != TC_OK) return ret;

  if (fVerbose) {
    std::cout << "Check read: " << std::endl;
    std::cout << "0) check: " << int(check0) << "\t old val: " << int(byte0)
              << std::endl;
    std::cout << "1) check: " << int(check1) << "\t old val: " << int(byte1)
              << std::endl;
  }
  if (check0 != byte0) {
    return TC_UNEXPECTED_RESPONSE;
  }
  if (check1 != byte1) {
    return TC_UNEXPECTED_RESPONSE;
  }
  return TC_OK;
}  // mapping SP to enable bit

int TargetModule::EnableHVSuperPixel(uint8_t superPixel) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "ERROR: This function is only implemented for kTCModule and "
                 "kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }

  int ret;
  int enableBit = SuperPixelIdToHVEneableBit(superPixel);
  if (enableBit < 0) return TC_UNEXPECTED_RESPONSE;

  // read current byte
  uint8_t byte0, byte1;
  if ((ret = ReadHVEnableBytes(byte0, byte1)) != TC_OK) return ret;

  if (fVerbose) {
    std::cout << "First read: " << std::endl;
    std::cout << "0) " << int(byte0) << std::endl;
    std::cout << "1) " << int(byte1) << std::endl;
  }
  // modify bytes to enable bit
  if (enableBit < 8) {
    uint8_t specBit = 1 << enableBit;
    if (!(specBit & byte0)) {  // check if bit is up
      byte0 = specBit | byte0;
    }
  } else {
    enableBit -= 8;
    uint8_t specBit = 1 << enableBit;
    if (!(specBit & byte1)) {  // check if bit is up
      byte1 = specBit | byte1;
    }
  }

  // Set the 7 bit device address of the I/0 expander on power board
  // 0b0100001 is I2C bus of the I/0 expander (TI PCA9555)
  if ((ret = WriteSetting("I2CAddr_Power", 0b0100001)) != TC_OK) return ret;

  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Power", 0)) != TC_OK) return ret;

  // not sure why this block is needed..
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x6)) != TC_OK) return ret;
  if ((ret = WriteSetting("I2CWriteData_Power", 0)) != TC_OK) return ret;
  //    std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x7)) != TC_OK) return ret;
  if ((ret = WriteSetting("I2CWriteData_Power", 0)) != TC_OK) return ret;

  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;
  // not sure why this block is needed..

  // Writing enable byte 0
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x2)) != TC_OK) return ret;
  if ((ret = WriteSetting("I2CWriteData_Power", byte0)) != TC_OK) return ret;
  //    std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;
  // writing byte 1
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x3)) != TC_OK) return ret;
  if ((ret = WriteSetting("I2CWriteData_Power", byte1)) != TC_OK) return ret;

  //    std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;
  usleep(1e5);

  // reading back bytes
  // reading back bytes for checking
  uint8_t check0, check1;
  if ((ret = ReadHVEnableBytes(check0, check1)) != TC_OK) return ret;

  if (fVerbose) {
    std::cout << "Check read: " << std::endl;
    std::cout << "0) check: " << int(check0) << "\t old val: " << int(byte0)
              << std::endl;
    std::cout << "1) chekc: " << int(check1) << "\t old val: " << int(byte1)
              << std::endl;
  }
  if (check0 != byte0) {
    return TC_UNEXPECTED_RESPONSE;
  }
  if (check1 != byte1) {
    return TC_UNEXPECTED_RESPONSE;
  }

  return TC_OK;
}  // mapping SP to enable bit

/////////////////////////////////////
int TargetModule::DisableHVAll() {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "TargetModule ERROR: This function is only implemented for "
                 "kTCModule and kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }

  int ret;
  // Set the 7 bit device address of the I/0 expander on power board
  // 0b0100001 is I2C bus of the I/0 expander (TI PCA9555)
  if ((ret = WriteSetting("I2CAddr_Power", 0b0100001)) != TC_OK) return ret;

  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Power", 0)) != TC_OK) return ret;

  // Writing enable byte 0
  // Set the 8 bit register address, you want to excess on the device with read
  // or write, transmits msb first, 0x2 is output port 0 on the I/0 expander
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x6)) != TC_OK) return ret;
  // write two bytes enable mask
  //        if ( (ret = WriteSetting("I2CWriteData_Power",0)) != TC_OK)
  //        return ret;
  if ((ret = WriteSetting("I2CWriteData_Power", 0)) != TC_OK) return ret;

  // Starts the operation, non sticky
  //        std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  // Writing enable byte 0
  // Set the 8 bit register address, you want to excess on the device with read
  // or write, transmits msb first, 0x2 is output port 0 on the I/0 expander
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x7)) != TC_OK) return ret;
  // write two bytes enable mask
  //        if ( (ret = WriteSetting("I2CWriteData_Power",0)) != TC_OK)
  //        return ret;
  if ((ret = WriteSetting("I2CWriteData_Power", 0)) != TC_OK) return ret;
  // Starts the operation, non sticky
  //        std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  // Writing enable byte 0
  // Set the 8 bit register address, you want to excess on the device with read
  // or write, transmits msb first, 0x2 is output port 0 on the I/0 expander
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x2)) != TC_OK) return ret;
  // write two bytes enable mask
  //        if ( (ret = WriteSetting("I2CWriteData_Power",0)) != TC_OK)
  //        return ret;
  if ((ret = WriteSetting("I2CWriteData_Power", 0)) != TC_OK) return ret;
  // Starts the operation, non sticky
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  // Writing enable byte 1
  // Set the 8 bit register address, you want to excess on the device with read
  // or write, transmits msb first, 0x2 is output port 0 on the I/0 expander
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x3)) != TC_OK) return ret;
  // write two bytes enable mask
  if ((ret = WriteSetting("I2CWriteData_Power", 0)) != TC_OK) return ret;

  // Starts the operation, non sticky
  //        std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  // read back the value we just have written
  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Power", 1)) != TC_OK) return ret;

  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  uint32_t answer = 0xFFFFFFFF;
  if ((ret = ReadSetting("I2CReadData_Power", answer)) != TC_OK) return ret;

  if (answer != 0) {
    std::cout << "Error unexpected answer while reading enable mask"
              << std::endl;
    return TC_UNEXPECTED_RESPONSE;
  }
  return TC_OK;
}

/////////////////////////////////////
int TargetModule::EnableHVAll() {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "TargetModule ERROR: This function is only implemented for "
                 "kTCModule and kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }

  int ret;
  // Set the 7 bit device address of the I/0 expander on power board
  // 0b0100001 is I2C bus of the I/0 expander (TI PCA9555)
  if ((ret = WriteSetting("I2CAddr_Power", 0b0100001)) != TC_OK) return ret;

  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Power", 0)) != TC_OK) return ret;

  // Writing enable byte 0
  // Set the 8 bit register address, you want to excess on the device with read
  // or write, transmits msb first, 0x2 is output port 0 on the I/0 expander
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x6)) != TC_OK) return ret;
  // write two bytes enable mask
  if ((ret = WriteSetting("I2CWriteData_Power", 0)) != TC_OK) return ret;

  // Starts the operation, non sticky
  //    std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  // Writing enable byte 0
  // Set the 8 bit register address, you want to excess on the device with read
  // or write, transmits msb first, 0x2 is output port 0 on the I/0 expander
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x7)) != TC_OK) return ret;
  // write two bytes enable mask
  if ((ret = WriteSetting("I2CWriteData_Power", 0)) != TC_OK) return ret;

  // Starts the operation, non sticky
  //    std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  // Writing enable byte 0
  // Set the 8 bit register address, you want to excess on the device with read
  // or write, transmits msb first, 0x2 is output port 0 on the I/0 expander
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x2)) != TC_OK) return ret;
  // write two bytes enable mask
  if ((ret = WriteSetting("I2CWriteData_Power", 0xFF)) != TC_OK) return ret;

  // Starts the operation, non sticky
  //   std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  // Writing enable byte 1
  // Set the 8 bit register address, you want to excess on the device with read
  // or write, transmits msb first, 0x2 is output port 0 on the I/0 expander
  if ((ret = WriteSetting("I2CRegAddr_Power", 0x3)) != TC_OK) return ret;
  // write two bytes enable mask
  if ((ret = WriteSetting("I2CWriteData_Power", 0xFF)) != TC_OK) return ret;
  //    WriteSetting("I2CWriteData_Power",0xFF);
  // Starts the operation, non sticky
  //    std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  // read back the value we just have written
  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Power", 1)) != TC_OK) return ret;

  // Starts the operation, non sticky
  //   std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;
  // read back both enable0 and enable1 bytes
  uint32_t answer = 0;
  if ((ret = ReadSetting("I2CReadData_Power", answer)) != TC_OK) return ret;
  if (answer != 0xFFFF) {
    std::cout << "Error unexpected answer while reading enable mask"
              << std::endl;
    return TC_UNEXPECTED_RESPONSE;
  }
  return TC_OK;
}

// HV regulator control settings
// Initialize Write HVDAC 0
int TargetModule::SetHVDAC(uint8_t superPixel, uint8_t val) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "ERROR: This function is only implemented for kTCModule and "
                 "kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }
  int ret;

  int i2cAddr = SuperPixelIdToI2CAddr(superPixel);
  if (i2cAddr < 0) {
    return TC_ERR_USER_ERROR;
  }
  if ((ret = WriteSetting("I2CAddr_Power", i2cAddr)) != TC_OK) return ret;

  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Power", 0)) != TC_OK) return ret;

  int regAddr = SuperPixelIdToI2CRegAddr(superPixel);
  if (regAddr < 0) {
    return TC_ERR_USER_ERROR;
  }

  if ((ret = WriteSetting("I2CRegAddr_Power", regAddr + 16)) != TC_OK)
    return ret;

  // write two bytes enable mask
  if ((ret = WriteSetting("I2CWriteData_Power", val)) != TC_OK) return ret;
  //  WriteSetting("I2CWriteData_Power",val);

  // Starts the operation, non sticky
  //  std::cout << "expected error, non sticky bit" << std::endl;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  uint8_t checkVal;
  if ((ret = ReadHVDAC(superPixel, checkVal)) != TC_OK) return ret;

  if (checkVal != val) {
    std::cout << "Written HV dac value differ from readback dac value"
              << std::endl;
    return TC_UNEXPECTED_RESPONSE;
  }

  return TC_OK;
}

int TargetModule::ReadHVDAC(uint8_t superPixel, uint8_t& val) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "ERROR: This function is only implemented for kTCModule and "
                 "kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }
  int ret;
  // device
  int i2cAddr = SuperPixelIdToI2CAddr(superPixel);
  if (i2cAddr < 0) {
    return TC_ERR_USER_ERROR;
  }
  if ((ret = WriteSetting("I2CAddr_Power", i2cAddr)) != TC_OK) return ret;

  // 0 write, 1 read
  if ((ret = WriteSetting("I2CRW_Power", 0)) != TC_OK) return ret;

  // pin on device
  int regAddr = SuperPixelIdToI2CRegAddr(superPixel);
  if (regAddr < 0) {
    return TC_ERR_USER_ERROR;
  }

  if ((ret = WriteSetting("I2CRegAddr_Power", regAddr | 48)) != TC_OK)
    return ret;

  // write two bytes enable mask
  if ((ret = WriteSetting("I2CWriteData_Power", 3)) != TC_OK) return ret;
  //  WriteSetting("I2CWriteData_Power",3);

  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  // perform the read action in device
  if ((ret = WriteSetting("I2CAddr_Power", i2cAddr)) != TC_OK) return ret;
  if ((ret = WriteSetting("I2CRW_Power", 1)) != TC_OK) return ret;
  if ((ret = WriteSetting("I2CStart_Power", 1)) != TC_OK) return ret;

  uint32_t tempVal;
  if ((ret = ReadSetting("I2CReadData_Power", tempVal)) != TC_OK) return ret;

  val = uint8_t(tempVal);

  return TC_OK;
}

int TargetModule::SetHVDACAll(uint8_t dacVal) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "ERROR: This function is only implemented for kTCModule and "
                 "kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }
  int ret;
  for (uint8_t superPixel = 0; superPixel < 16; superPixel++) {
    if ((ret = SetHVDAC(superPixel, dacVal)) != TC_OK) return ret;
  }

  std::cout << "SetHVDACAll " << (int)dacVal << std::endl;

  return TC_OK;
}

int TargetModule::SuperPixelIdToI2CAddr(uint8_t spId) {
  if (spId == 0 || spId == 1 || spId == 2 || spId == 3) {
    return 0b0100000;
  } else if (spId == 4 || spId == 9 || spId == 10 || spId == 6) {
    return 0b0101111;
  } else if (spId == 5 || spId == 7 || spId == 8 || spId == 11) {
    return 0b0101100;
  } else if (spId == 12 || spId == 13 || spId == 14 || spId == 15) {
    return 0b0100011;
  } else {
    return -1;
  }
}

int TargetModule::SuperPixelIdToI2CRegAddr(uint8_t spId) {
  if (spId == 1 || spId == 4 || spId == 11 || spId == 12) {
    return 0b0000;
  } else if (spId == 0 || spId == 5 || spId == 9 || spId == 15) {
    return 0b0001;
  } else if (spId == 2 || spId == 6 || spId == 7 || spId == 13) {
    return 0b0010;
  } else if (spId == 3 || spId == 8 || spId == 10 || spId == 14) {
    return 0b0011;
  } else {
    return -1;
  }
}

int TargetModule::SuperPixelIdToHVEneableBit(uint8_t spId) {
  if (spId == 0) {
    return 3;
  } else if (spId == 1) {
    return 0;
  } else if (spId == 2) {
    return 1;
  } else if (spId == 3) {
    return 2;
  } else if (spId == 4) {
    return 4;
  } else if (spId == 5) {
    return 8;
  } else if (spId == 6) {
    return 5;
  } else if (spId == 7) {
    return 10;
  } else if (spId == 8) {
    return 9;
  } else if (spId == 9) {
    return 7;
  } else if (spId == 10) {
    return 6;
  } else if (spId == 11) {
    return 11;
  } else if (spId == 12) {
    return 15;
  } else if (spId == 13) {
    return 14;
  } else if (spId == 14) {
    return 13;
  } else if (spId == 15) {
    return 12;
  } else
    return -1;
}

//
int TargetModule::GetHVSuperPixel(uint8_t superPixel, float& val) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "ERROR: This function is only implemented for kTCModule and "
                 "kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }
  int ret;
  uint32_t answer;
  uint32_t answer2;
  if ((ret = ReadSetting("SlowADCEnable_Power", answer)) != TC_OK) return ret;
  if (answer != 1) {
    if ((ret = WriteSetting("SlowADCEnable_Power", 1)) != TC_OK) return ret;
    std::cout << "TargetModule::GetHVSuperPixel - sleep after enabling slow adc power" << std::endl;
    sleep(1);
  }
  char str[40];
  sprintf(str, "HV%d_Voltage", superPixel);
  if ((ret = ReadSetting(str, answer2)) != TC_OK) return ret;
  if (answer2 < 0x8000)
    answer2 += 0x8000;
  else
    answer2 = answer2 & 0x7FFF;
  val = answer2 * 0.03815 * 2 * 20 / 1000.;
  return TC_OK;
}

//
int TargetModule::ReadFromPrimaryEEPROM(uint8_t addrOnEEPROM, uint8_t& val) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "ERROR: This function is only implemented for kTCModule and "
                 "kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }
  int ret;
  // The Operation Code tells the EEPROM what to do, most important is 0xA
  // (0b1010) which performs EEPROM operation (R/W), see datasheet (table 5.1 on
  // page 12
  // http://www.atmel.com/images/Atmel-8903-SEEPROM-AT21CS01-Datasheet.pdf ) for
  // others, i assume never used
  if ((ret = WriteSetting("EepromOpCode_Primary", 0xA)) != TC_OK) return ret;

  // This sets the addres of the byte which will be written/read, 0-127
  if ((ret = WriteSetting("EepromRegAddr_Primary", addrOnEEPROM)) != TC_OK)
    return ret;

  // When this written a read operation will start, The content of EepromRegAddr
  // on EEPROM will be written to EepromReadByte
  if ((ret = WriteSetting("EepromStart_Primary", 0b110)) != TC_OK) return ret;

  // Read the answer from the EEPROM, data will be valid ca 1ms EepromStart
  // command.
  uint32_t answer;
  usleep(5e3);  // sleep 5 ms to be sure
  if ((ret = ReadSetting("EepromReadByte_Primary", answer)) != TC_OK)
    return ret;
  val = uint8_t(answer);
  // When true, EEPROM is not busy and can receive commands, and data in
  // EepromReadByte is valid. I say this will never be read back false.
  // HARM: Valid bit doesn't seem to work
  // if ( (ret = ReadSetting("EepromReadValid_Primary",answer)) != TC_OK) return
  // ret;
  //    if (!answer) {
  //      return TC_UNEXPECTED_RESPONSE;
  //    }
  return ret;
}

//
int TargetModule::WriteToPrimaryEEPROM(uint8_t addrOnEEPROM, uint8_t value) {
  if (!(fModuleType == kTCModule || fModuleType == kTCModuleBP)) {
    std::cout << "ERROR: This function is only implemented for kTCModule and "
                 "kTCModuleBP ";
    return TC_ERR_USER_ERROR;
  }
  int ret;
  // The Operation Code tells the EEPROM what to do, most important is 0xA
  // (0b1010) which performs EEPROM operation (R/W), see datasheet (table 5.1 on
  // page 12
  // http://www.atmel.com/images/Atmel-8903-SEEPROM-AT21CS01-Datasheet.pdf) for
  // others, i assume never used
  if ((ret = WriteSetting("EepromOpCode_Primary", 0xA)) != TC_OK) return ret;

  // This sets the addres of the byte which will be written/read, 0-127
  if ((ret = WriteSetting("EepromRegAddr_Primary", addrOnEEPROM)) != TC_OK)
    return ret;

  // Content to be written, 0-255
  if ((ret = WriteSetting("EepromWriteByte_Primary", value)) != TC_OK)
    return ret;

  // When this written, a write operation will start. The content of
  // EepromWriteByte will be written to EepromRegAddr on EEPROM
  if ((ret = WriteSetting("EepromStart_Primary", 0b101)) != TC_OK) return ret;

  return TC_OK;
}

}  // namespace TargetDriver
}  // namespace CTA
