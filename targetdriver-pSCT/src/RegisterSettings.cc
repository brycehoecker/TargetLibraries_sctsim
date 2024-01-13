// Copyright (c) 2015 The CTA Consortium. All rights reserved.

#include <stdlib.h>

#include <TargetDriver/UDPBase.h>
#include <bitset>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <limits>
#include <sstream>
#include <vector>

#include "TargetDriver/RegisterSettings.h"

namespace CTA {
namespace TargetDriver {

RegisterSettings::RegisterSettings(const std::string& pTargetFPGADefinitionFile,
                                   const std::string& pTargetASICDefinitionFile)
    : fDefintionFileFPGA(pTargetFPGADefinitionFile),
      fDefintionFileASIC(pTargetASICDefinitionFile),
      fDefintionFileTriggerASIC("") {
  if (fDefintionFileFPGA == "") {
    std::cerr
        << "WARNING: Initialization of RegisterSettings without FPGA def file"
        << std::endl;
  } else {
    ReadDefinitionFileFPGA();
    CheckFPGARegisterConsistency();
    ReadDefinitionFileASIC();
    CheckASICRegisterConsistency();
  }
}

RegisterSettings::RegisterSettings(
    const std::string& pTargetFPGADefinitionFile,
    const std::string& pTargetASICDefinitionFile,
    const std::string& pTargetTriggerASICDefinitionFile)
    : fDefintionFileFPGA(pTargetFPGADefinitionFile),
      fDefintionFileASIC(pTargetASICDefinitionFile),
      fDefintionFileTriggerASIC(pTargetTriggerASICDefinitionFile) {
  if (fDefintionFileFPGA == "") {
    std::cerr
        << "WARNING: Initialization of RegisterSettings without FPGA def file"
        << std::endl;
  } else {
    ReadDefinitionFileFPGA();
    CheckFPGARegisterConsistency();
    ReadDefinitionFileASIC();
    CheckASICRegisterConsistency();
    if (fDefintionFileTriggerASIC != "") {
      ReadDefinitionFileTriggerASIC();
      CheckTriggerASICRegisterConsistency();
    }
  }
}

int RegisterSettings::ReadDefinitionFileFPGA() {
  std::ifstream ifs(fDefintionFileFPGA.c_str());

  if (!ifs) {
    std::cerr << "**FATAL ERROR CANNOT OPEN " << fDefintionFileFPGA
              << " specify complete path to definition file " << std::endl;
    exit(-1);
  }

  std::string line;
  // HEADER
  while (getline(ifs, line)) {
    if (line[0] == '#') continue;
    if (line == "HEADER") break;
  }

  getline(ifs, line);
  std::stringstream ssType(line);
  std::string dum;
  ssType >> dum;
  if (dum != "TM_TYPE") {
    std::cerr << "EXPECTED TM_TYPE but read: " << dum << std::endl;
    exit(-1);
  }
  ssType >> fType;

  getline(ifs, line);
  std::stringstream ssFW(line);
  ssFW >> dum;
  if (dum != "TM_FIRMWARE_VERSION") {
    std::cerr << "EXPECTED TM_FIRMWARE_VERSION but read: " << dum << std::endl;
    exit(-1);
  }
  ssFW >> std::hex >> fFPGAFirmwareVersion;

  getline(ifs, line);
  std::stringstream ssDE(line);
  ssDE >> dum;
  if (dum != "DESCRIPTION") {
    std::cerr << "EXPECTED DESCRIPTION but read: " << dum << std::endl;
    exit(-1);
  }
  fFPGADescription = "";
  while (ssDE >> dum) {
    fFPGADescription += dum + " ";
  }

  getline(ifs, line);
  std::stringstream ssAU(line);
  ssAU >> dum;
  if (dum != "RESPONSIBLE_AUTHOR") {
    std::cerr << "EXPECTED RESPONSIBLE_AUTHOR but read: " << dum << std::endl;
    exit(-1);
  }
  ssAU >> fFPGAAuthor;

  getline(ifs, line);
  std::stringstream ssN(line);
  ssN >> dum;
  if (dum != "NUM_REGISTERS") {
    std::cerr << "EXPECTED NUM_REGISTERS but read: " << dum << std::endl;
    exit(-1);
  }
  ssN >> std::hex >> fFPGANumberOfRegisters;

  // SETTINGS
  while (getline(ifs, line)) {
    if (line[0] == '#') continue;
    if (line == "SETTINGS") break;
  }

  while (getline(ifs, line)) {
    if (line[0] == '#') continue;
    Setting setting;
    std::stringstream ss(line);
    std::string name;

    ss >> name;
    ss >> std::hex >> setting.regAddr;
    ss >> std::dec >> setting.nBits;
    ss >> std::dec >> setting.startBit;
    ss >> std::hex >> setting.value;
    //    ss >> setting.isReadOnly;
    uint16_t accessMode;
    ss >> accessMode;
    if (accessMode == 0) {
      setting.access = eRW;
    } else if (accessMode == 1) {
      setting.access = eR;
    } else if (accessMode == 2) {
      setting.access = eW;
    } else if (accessMode == 3) {
      setting.access = eRW_NS;
    } else {
      std::cerr << "Unknown AccesMode" << int(accessMode)
                << " in line: " << line << std::endl;
      exit(-1);
    }
    //    ss >> setting.access;
    ss >> std::hex >> setting.lowerBound;
    ss >> std::hex >> setting.upperBound;
    ss >> std::dec >> setting.multiplier;
    ss >> std::dec >> setting.offset;
    std::string word;
    while (ss >> word) setting.description += word + " ";

    if (setting.description.size() == 0) {
      // std::cerr << "WARNING: description missing for Setting: " << name
      //           << std::endl;
    }

    // if (setting.description[0] != '#') {
    //  std::cerr << "ERROR: comments in *.def file should start with a #, check
    //  "
    //             "this line for consistency: " << line << std::endl;
    //}

    AddFPGASetting(name, setting);
  }
  return TC_OK;
}

int RegisterSettings::ReadDefinitionFileTriggerASIC() {
  return ReadDefinitionFileASIC(true);
}

int RegisterSettings::ReadDefinitionFileASIC(bool isTriggerASIC) {
  std::ifstream ifs;
  if (!isTriggerASIC) {
    ifs.open(fDefintionFileASIC.c_str());
  } else
    ifs.open(fDefintionFileTriggerASIC.c_str());

  if (!ifs) {
    std::string filename = fDefintionFileASIC;
    if (isTriggerASIC) filename = fDefintionFileTriggerASIC;
    std::cerr << "FATAL ERROR CANNOT OPEN " << filename
              << " specify complete path to definition file " << std::endl;
    exit(-1);
  }

  std::string line;
  // HEADER
  while (getline(ifs, line)) {
    if (line[0] == '#') continue;
    if (line == "HEADER") break;
  }

  std::string dum;
  getline(ifs, line);
  std::stringstream ssDE(line);
  ssDE >> dum;
  if (dum != "DESCRIPTION") {
    std::cerr << "EXPECTED DESCRIPTION but read: " << dum << std::endl;
    exit(-1);
  }
  std::string descr = "";
  while (ssDE >> dum) {
    descr += dum + " ";
  }
  if (!isTriggerASIC) {
    fASICDescription = descr;
  } else {
    fTriggerASICDescription = descr;
  }

  getline(ifs, line);
  std::stringstream ssAU(line);
  ssAU >> dum;
  if (dum != "RESPONSIBLE_AUTHOR") {
    std::cerr << "EXPECTED RESPONSIBLE_AUTHOR but read: " << dum << std::endl;
    exit(-1);
  }
  std::string author = "";
  while (ssAU >> dum) {
    author += dum + " ";
  }
  if (!isTriggerASIC) {
    fASICAuthor = author;
  } else {
    fTriggerASICAuthor = author;
  }

  getline(ifs, line);
  std::stringstream ssN(line);
  ssN >> dum;
  if (dum != "NUM_REGISTERS") {
    std::cerr << "EXPECTED NUM_REGISTERS but read: " << dum << std::endl;
    exit(-1);
  }
  if (!isTriggerASIC) {
    ssN >> std::hex >> fASICNumberOfRegisters;
  } else {
    ssN >> std::hex >> fTriggerASICNumberOfRegisters;
  }
  // SETTINGS
  while (getline(ifs, line)) {
    if (line[0] == '#') continue;
    if (line == "SETTINGS") break;
  }

  while (getline(ifs, line)) {
    if (line[0] == '#') continue;

    Setting setting;
    std::stringstream ss(line);
    std::string name;

    ss >> name;
    ss >> std::hex >> setting.regAddr;
    ss >> std::dec >> setting.nBits;
    ss >> std::dec >> setting.startBit;
    ss >> std::hex >> setting.value;
    //    ss >> setting.isReadOnly;
    //    ss >> setting.access;
    uint16_t accessMode;
    ss >> accessMode;
    if (accessMode == 0) {
      setting.access = eRW;
    } else if (accessMode == 1) {
      setting.access = eR;
    } else if (accessMode == 2) {
      setting.access = eW;
    } else if (accessMode == 3) {
      setting.access = eRW_NS;
    } else {
      std::cerr << "Unknown AccesMode in " << line << std::endl;
      exit(-1);
    }

    ss >> std::hex >> setting.lowerBound;
    ss >> std::hex >> setting.upperBound;
    ss >> std::dec >> setting.multiplier;
    ss >> std::dec >> setting.offset;

    if (ss.bad()) {
      std::cerr << "ERROR: Could not parse a line" << std::endl;
      std::cerr << line << std::endl;
      exit(-1);
    }

    std::string word;
    while (ss >> word) setting.description += word + " ";

    if (setting.description.size() == 0) {
      // std::cerr << "WARNING: description missing for Setting: " << name
      //           << std::endl;
    }
    SettingASIC asicSettings;
    for (int i = 0; i < 4; ++i) asicSettings.settingASIC[i] = setting;
    AddASICSetting(name, asicSettings, isTriggerASIC);
  }
  return TC_OK;
}

int RegisterSettings::CheckFPGARegisterConsistency() {
  /// CHECK THE TOTAL NUMBER OF REGISTERS
  if (fFPGANumberOfRegisters != fRegisterMapFPGA.size()) {
    std::cerr << "ERROR: number of FPGA registers (" << std::hex
              << fRegisterMapFPGA.size()
              << ") doesn't correspond to the value "
                 "specified in the HEADER: "
              << fFPGANumberOfRegisters << std::endl;
  }

  /// CHECK FOR MISSING REGISTER
  RF_cit itReg = fRegisterMapFPGA.cbegin();
  std::vector<uint32_t> vMissingRegisters;
  uint32_t iMiss = 0;
  // TODO(Harm): Use normal for loop
  while (itReg != fRegisterMapFPGA.cend()) {
    //    std::cout << itReg->first << "\t" << itReg->second.val << std::endl;
    if (itReg->first != iMiss) {
      vMissingRegisters.push_back(iMiss);
    } else {
      ++iMiss;
    }

    ++itReg;
  }

  if (vMissingRegisters.size() != 0) {
    std::cerr << "ERROR: missing registers FPGA in *.def file : ";
    std::cerr << "First Missing register is: 0x" << std::hex
              << vMissingRegisters[0] << std::endl;
    // TODO(Harm): Don't use exit
    exit(-1);
  }

  /// CHECK THAT ALL BITS ARE IN SETTINGS MAP
  itReg = fRegisterMapFPGA.cbegin();
  // TODO(Harm): Use normal for loop
  while (itReg != fRegisterMapFPGA.cend()) {
    std::vector<Setting> vSet;
    typedef std::vector<Setting>::const_iterator v_cit;
    for (SF_cit itSet = fSettingMapFPGA.begin(); itSet != fSettingMapFPGA.end();
         ++itSet) {
      if (itSet->second.regAddr == itReg->first) {
        vSet.push_back(itSet->second);
      }
    }  // all setting for a register
    std::vector<bool> vAreSet(32, false);
    typedef std::vector<bool>::const_iterator vA_cit;
    for (v_cit cit = vSet.cbegin(); cit != vSet.cend(); ++cit) {
      for (uint16_t ibit = cit->startBit; ibit < (cit->startBit + cit->nBits);
           ++ibit) {
        if (vAreSet[ibit]) {
          std::cerr << "ERROR: bit " << std::dec << ibit
                    << " in FPGA register 0x" << std::hex << cit->regAddr
                    << " all ready set, check definition file for overlapping "
                       "settings ("
                    << fDefintionFileFPGA << ")" << std::dec << std::endl;
          exit(-1);
        } else {
          vAreSet[ibit] = true;
        }
      }
    }
    /// are all bit set?
    bool allSet = true;
    for (vA_cit cit = vAreSet.cbegin(); cit != vAreSet.cend(); ++cit) {
      if (*cit != true) allSet = false;
    }
    if (!allSet) {
      std::cerr << "ERROR: missing bits in FPGA register 0x" << std::hex
                << itReg->first << std::dec << std::endl;
      std::cerr << "bit\tSet?" << std::endl;
      for (vA_cit cit = vAreSet.cbegin(); cit != vAreSet.cend(); ++cit) {
        std::cerr << std::distance(vAreSet.cbegin(), cit) << "\t" << *cit
                  << std::endl;
      }
      exit(-1);
    }  // all set
    ++itReg;
  }

  return TC_OK;
}

int RegisterSettings::CheckTriggerASICRegisterConsistency() {
  return CheckASICRegisterConsistency(true);
}

int RegisterSettings::CheckASICRegisterConsistency(bool isTriggerASIC) {
  /// CHECK THE TOTAL NUMBER OF REGISTERS
  if (!isTriggerASIC) {
    if (fASICNumberOfRegisters != fRegisterMapASIC.size()) {
      std::cerr << "ERROR: number of ASIC registers (" << std::hex
                << fRegisterMapASIC.size()
                << ") doesn't correspond to the value "
                   "specified in the HEADER: "
                << fASICNumberOfRegisters << std::endl;
    }
  } else {
    if (fTriggerASICNumberOfRegisters != fRegisterMapTriggerASIC.size()) {
      std::cerr << "ERROR: number of TRIGGER ASIC registers (" << std::hex
                << fRegisterMapTriggerASIC.size()
                << ") doesn't correspond to the value "
                   "specified in the HEADER: "
                << fTriggerASICNumberOfRegisters << std::endl;
    }
  }

  std::map<uint8_t, RegisterASIC>::iterator itReg;
  std::map<uint8_t, RegisterASIC>::iterator endReg;
  if (!isTriggerASIC) {
    itReg = fRegisterMapASIC.begin();
    endReg = fRegisterMapASIC.end();
  } else {
    itReg = fRegisterMapTriggerASIC.begin();
    endReg = fRegisterMapTriggerASIC.end();
  }

  /// CHECK FOR MISSING REGISTER
  std::vector<uint8_t> vMissingRegisters;
  uint8_t iMiss = 0;
  // TODO(Harm): Use normal for loop
  while (itReg != endReg) {
    //    std::cout << itReg->first << "\t" << itReg->second.val << std::endl;
    if (itReg->first != iMiss) {
      vMissingRegisters.push_back(iMiss);
    } else {
      ++iMiss;
    }

    ++itReg;
  }
  if (vMissingRegisters.size() != 0) {
    std::cerr << "ERROR: missing registers in ASIC *.def file : ";
    std::cerr << "First Missing register is: 0x" << std::hex
              << vMissingRegisters[0] << std::endl;
    exit(-1);
  }

  /// CHECK THAT ALL BITS ARE IN SETTINGS MAP
  if (!isTriggerASIC) {
    itReg = fRegisterMapASIC.begin();
  } else {
    itReg = fRegisterMapTriggerASIC.begin();
  }

  // TODO(Harm): Use normal for loop
  while (itReg != endReg) {
    std::vector<Setting> vSet;
    typedef std::vector<Setting>::const_iterator v_cit;
    std::map<std::string, SettingASIC>::iterator itSet;
    std::map<std::string, SettingASIC>::iterator endSet, beginSet;
    if (!isTriggerASIC) {
      beginSet = fSettingMapASIC.begin();
      endSet = fSettingMapASIC.end();
    } else {
      beginSet = fSettingMapTriggerASIC.begin();
      endSet = fSettingMapTriggerASIC.end();
    }

    for (itSet = beginSet; itSet != endSet; ++itSet) {
      if (itSet->second.settingASIC[0].regAddr == itReg->first)
        vSet.push_back(itSet->second.settingASIC[0]);
    }  // all setting for a register
    std::vector<bool> vAreSet(12, false);
    typedef std::vector<bool>::const_iterator vA_cit;
    for (v_cit cit = vSet.cbegin(); cit != vSet.cend(); ++cit) {
      for (uint16_t ibit = cit->startBit; ibit < (cit->startBit + cit->nBits);
           ++ibit) {
        if (vAreSet[ibit]) {
          std::string sDefFile;
          if (!isTriggerASIC) {
            sDefFile = fDefintionFileASIC;
          } else {
            sDefFile = fDefintionFileTriggerASIC;
          }
          std::cerr << "ERROR: bit " << std::dec << ibit
                    << " in ASIC register 0x" << std::hex << cit->regAddr
                    << " all ready set, check definition file for overlapping "
                       "settings ("
                    << sDefFile << ")" << std::dec << std::endl;
          exit(-1);
        } else {
          vAreSet[ibit] = true;
        }
      }
    }
    /// are all bit set?
    bool allSet = true;
    for (vA_cit cit = vAreSet.cbegin(); cit != vAreSet.cend(); ++cit) {
      if (*cit != true) {
        allSet = false;
      }
    }
    if (!allSet) {
      std::cerr << "ERROR: missing bits in ASIC register " << std::hex
                << itReg->first << std::dec << std::endl;
      std::cerr << "bit\tSet?" << std::endl;
      for (unsigned int i = 0; i < vAreSet.size(); ++i) {
        std::cerr << i << "\t" << vAreSet[i] << std::endl;
      }
      exit(-1);
    }  // all set
    ++itReg;
  }

  return TC_OK;
}

bool RegisterSettings::CheckRegisterPartially(uint32_t pRegisterValue,
                                              Setting pSetting) {
  // get part of the register we are want to check
  uint32_t select;
  if (pSetting.nBits == 32) {
    select = 0;
    select = ~select;
  } else {
    select = ((uint32_t((1 << pSetting.nBits) - 1)) << pSetting.startBit);
  }
  //  std::cout << "REG: " << std::bitset<32>(reg) << std::endl;
  //  std::cout << "select: " <<  std::bitset<32>(select) << std::endl;
  pRegisterValue = pRegisterValue & select;
  pRegisterValue =
      pRegisterValue >>
      pSetting.startBit;  // shift them towards to end and compare them
  if (pSetting.value != pRegisterValue) {
    std::cout << "CheckRegisterPartially Setting Value: " << std::hex
              << pSetting.value
              << " it should be (register value): " << pRegisterValue
              << std::endl;
    return false;
  }
  return true;
}

void RegisterSettings::GetRegisterPartially(uint32_t pRegisterValue,
                                            Setting pSetting,
                                            uint32_t& pPartialRegisterValue) {
  // get part of the register we are want to check
  uint32_t select = 0;
  if (pSetting.nBits == 32) {
    select = ~select;
  } else {
    select = ((uint32_t((1 << pSetting.nBits) - 1)) << pSetting.startBit);
  }
  pRegisterValue = pRegisterValue & select;
  // shift them towards to end
  pPartialRegisterValue = pRegisterValue >> pSetting.startBit;
}

void RegisterSettings::ModifyRegisterPartially(uint32_t& reg, Setting set) {
  // check if value is not larger that nBits
  if (set.value >= uint32_t(1 << set.nBits)) {
    std::cerr << "ERROR: don't be silly, you can not fit in " << std::dec
              << set.value << " in " << set.nBits
              << " bits ( register: " << std::hex
              << static_cast<int64_t>(set.regAddr) << std::dec << ")"
              << std::endl;
    PrintSetting(set);
    exit(-1);
  }
  // clean out the bits that we want to overwrite
  uint32_t clean = ~((uint32_t((1 << set.nBits) - 1)) << set.startBit);
  reg = reg & clean;
  // shift the new values towards the start bit
  uint32_t shiftedVal = set.value << set.startBit;
  // update the cleaned register
  reg = reg | shiftedVal;
}

int RegisterSettings::AddFPGASetting(const std::string& name, Setting setting) {
  std::map<std::string, Setting>::iterator itSet;
  itSet = fSettingMapFPGA.find(name);
  if (itSet != fSettingMapFPGA.end()) {
    std::cerr << "WARNING: < " << name
              << " > Setting already there check "
                 "definition file for duplicated "
                 "settings"
              << std::endl;
    return 0;
  }
  // updating fSettingMapFPGA
  fSettingMapFPGA[name] = setting;

  // register can already be partially set.
  // if not, the part that is not written yet
  // will be filled with zeroes
  std::map<uint32_t, RegisterFPGA>::iterator itReg;
  itReg = fRegisterMapFPGA.find(setting.regAddr);

  RegisterFPGA reg;
  reg.val = 0;

  if (itReg != fRegisterMapFPGA.end()) {
    reg.val = fRegisterMapFPGA[setting.regAddr].val;
    //    reg.isReadOnly = setting.isReadOnly;
    reg.access = setting.access;
  }

  // checking if we have to set the full register
  if (setting.nBits == 0x20 && setting.startBit == 0) {
    reg.val = setting.value;
  } else {  // Filling the register partially
    ModifyRegisterPartially(reg.val, setting);
  }

  // update value
  fRegisterMapFPGA[setting.regAddr] = reg;
  return 0;
}

int RegisterSettings::UpdateFPGASettingMapFromRegisterMap() {
  for (SF_cit it = fSettingMapFPGA.begin(); it != fSettingMapFPGA.end(); it++) {
    uint32_t regVal = fRegisterMapFPGA[it->second.regAddr].val;
    uint32_t setVal;
    GetRegisterPartially(regVal, it->second, setVal);
    fSettingMapFPGA[it->first].value = setVal;
  }
  return TC_OK;
}

int RegisterSettings::AddTriggerASICSetting(const std::string& name,
                                            SettingASIC setting) {
  return AddASICSetting(name, setting, true);
}

int RegisterSettings::AddASICSetting(const std::string& name,
                                     SettingASIC setting, bool isTriggerASIC) {
  std::map<std::string, SettingASIC>::iterator itSet, itEnd;
  if (!isTriggerASIC) {
    itEnd = fSettingMapASIC.end();
    itSet = fSettingMapASIC.find(name);
  } else {
    itEnd = fSettingMapTriggerASIC.end();
    itSet = fSettingMapTriggerASIC.find(name);
  }

  if (itSet != itEnd) {
    std::cerr << "WARNING: < " << name
              << " > Setting already there check "
                 "definition file for duplicated "
                 "settings"
              << std::endl;
    return TC_ERR_CONF_FAILURE;
  }

  uint16_t max12bit = (1 << 12);
  for (int i = 0; i < 4; ++i) {
    if (setting.settingASIC[i].value > max12bit) {
      std::cerr << "ERROR: ASIC setting <" << name
                << "> has a value larger than 12 bits. This is not allowed"
                << std::endl;
    }
  }

  // updating fSettingMapASIC
  if (!isTriggerASIC) {
    fSettingMapASIC[name] = setting;
  } else {
    fSettingMapTriggerASIC[name] = setting;
  }
  // register can already be partially set.
  // if not, the part that is not written yet
  // will be filled with zeroes

  RegisterASIC asicReg;
  for (uint8_t asic = 0; asic < 4; ++asic) {
    asicReg.val[asic] = 0;
  }

  uint8_t regAddr = static_cast<uint8_t>(setting.settingASIC[0].regAddr);
  std::map<uint8_t, RegisterASIC>::iterator itReg, endReg;
  if (!isTriggerASIC) {
    itReg = fRegisterMapASIC.find(regAddr);
    endReg = fRegisterMapASIC.end();
    // if doesnot exist, fill with zeros
    if (itReg == endReg) {
      fRegisterMapASIC[regAddr] = asicReg;
    } else
      asicReg = fRegisterMapASIC[regAddr];
  } else {
    itReg = fRegisterMapTriggerASIC.find(regAddr);
    endReg = fRegisterMapTriggerASIC.end();
    // if doesnot exist, fill with zeros
    if (itReg == endReg) {
      fRegisterMapTriggerASIC[regAddr] = asicReg;
    } else
      asicReg = fRegisterMapTriggerASIC[regAddr];
  }

  // loop over the 4 asic and update the setting
  for (uint8_t asic = 0; asic < 4; ++asic) {
    Setting set = setting.settingASIC[asic];
    if (set.nBits == 0x0C && set.startBit == 0) {
      asicReg.val[asic] = static_cast<uint16_t>(set.value);
    } else {  // Filling the register partially
      uint32_t reg = asicReg.val[asic];
      ModifyRegisterPartially(reg, set);
      asicReg.val[asic] = uint16_t(reg);
    }
  }

  // update register map
  if (!isTriggerASIC) {
    fRegisterMapASIC[regAddr] = asicReg;
  } else {
    fRegisterMapTriggerASIC[regAddr] = asicReg;
  }
  return TC_OK;
}

int RegisterSettings::ReadUserFPGAConfigFile(const std::string& configFile) {
  std::ifstream ifs(configFile.c_str());
  if (!ifs) {
    std::cerr << "FATAL ERROR CANNOT OPEN " << configFile
              << " specify complete path to user config-file " << std::endl;
    exit(-1);
  }

  std::string line;
  while (getline(ifs, line)) {
    if (line[0] == '#') continue;
    std::stringstream ss(line);
    std::string name;
    ss >> name;
    uint32_t val;
    ss >> std::hex >> val;
    ModifyFPGASetting(name, val);
  }
  return TC_OK;
}

int RegisterSettings::ReadUserTriggerASICConfigFile(
    const std::string& configFile) {
  return ReadUserASICConfigFile(configFile, true);
}

int RegisterSettings::ReadUserASICConfigFile(const std::string& configFile,
                                             bool isTriggerASIC) {
  std::ifstream ifs(configFile.c_str());
  if (!ifs) {
    std::cerr << "FATAL ERROR CANNOT OPEN " << configFile
              << " specify complete path to user config-file " << std::endl;
    exit(-1);
  }

  std::string line;
  while (getline(ifs, line)) {
    if (line[0] == '#') continue;
    std::stringstream ss(line);
    std::string name;
    ss >> name;
    uint16_t val;
    ss >> std::hex >> val;
    ModifyASICSetting(name, 0, val, isTriggerASIC);
    ss >> std::hex >> val;
    ModifyASICSetting(name, 1, val, isTriggerASIC);
    ss >> std::hex >> val;
    ModifyASICSetting(name, 2, val, isTriggerASIC);
    ss >> std::hex >> val;
    ModifyASICSetting(name, 3, val, isTriggerASIC);
  }

  return TC_OK;
}

int RegisterSettings::ModifyTriggerASICSetting(const std::string& name,
                                               uint8_t asic, uint16_t newVal) {
  return ModifyASICSetting(name, asic, newVal, true);
}

int RegisterSettings::ModifyASICSetting(const std::string& name, uint8_t asic,
                                        uint16_t newVal, bool isTriggerASIC) {
  if (asic > 3 || asic < 0) {
    std::cerr << "ASIC must be smaller than 4" << std::endl;
    exit(-1);
  }

  std::map<std::string, SettingASIC>::iterator it;
  if (!isTriggerASIC) {
    it = fSettingMapASIC.find(name);
    if (it != fSettingMapASIC.end()) {
      uint16_t max12bit = (1 << 12);
      if (newVal > max12bit) {
        std::cerr << "ERROR: trying to set a value larger than 12 bits"
                  << std::endl;
        exit(-1);
      }
      // update setting map
      if (fSettingMapASIC.find(name) != fSettingMapASIC.end()) {
        fSettingMapASIC[name].settingASIC[asic].value = newVal;
      } else {
        std::cerr << "ERROR: trying to modify a setting that not in the "
                     "register map!! "
                  << std::endl;
        exit(-1);
      }

      Setting setting = fSettingMapASIC[name].settingASIC[asic];

      std::map<uint8_t, RegisterASIC>::iterator itReg;
      itReg = fRegisterMapASIC.find(static_cast<uint8_t>(setting.regAddr));
      uint32_t val = 0;
      if (itReg != fRegisterMapASIC.end()) val = itReg->second.val[asic];
      // checking if we have to set the full register
      if (setting.nBits == 0x0C && setting.startBit == 0) {
        val = setting.value;
      } else {  // Filling the register partially
        ModifyRegisterPartially(val, setting);
      }
      // update
      itReg->second.val[asic] = uint16_t(val);

    } else {
      std::cerr << "ERROR: undefined setting name in ASIC definition file: "
                << name << std::endl;
      //      exit(-1);
    }
  } else {
    it = fSettingMapTriggerASIC.find(name);
    if (it != fSettingMapTriggerASIC.end()) {
      uint16_t max12bit = (1 << 12);
      if (newVal > max12bit) {
        std::cerr << "ERROR: trying to set a value larger than 12 bits"
                  << std::endl;
        return TC_ERR_CONF_FAILURE;
      }
      // update setting map
      // update setting map
      if (fSettingMapTriggerASIC.find(name) != fSettingMapTriggerASIC.end()) {
        fSettingMapTriggerASIC[name].settingASIC[asic].value = newVal;
      } else {
        std::cerr << "ERROR: trying to modify a setting that not in the  "
                     "trigger register map!! "
                  << std::endl;
        return TC_ERR_CONF_FAILURE;
      }

      Setting setting = fSettingMapTriggerASIC[name].settingASIC[asic];
      // getting the register
      std::map<uint8_t, RegisterASIC>::iterator itReg;
      itReg =
          fRegisterMapTriggerASIC.find(static_cast<uint8_t>(setting.regAddr));
      uint32_t val = 0;
      if (itReg != fRegisterMapTriggerASIC.end()) val = itReg->second.val[asic];
      // checking if we have to set the full register
      if (setting.nBits == 0x0C && setting.startBit == 0) {
        val = setting.value;
      } else {  // Filling the register partially
        ModifyRegisterPartially(val, setting);
      }
      // update
      itReg->second.val[asic] = uint16_t(val);

    } else {
      std::cerr << "ERROR: undefined setting name in ASIC definition file: "
                << name << std::endl;
      //      exit(-1);
    }
  }

  return TC_OK;
}

int RegisterSettings::ModifyFPGASetting(const std::string& name,
                                        uint32_t newVal) {
  std::map<std::string, Setting>::iterator it;
  it = fSettingMapFPGA.find(name);
  if (it != fSettingMapFPGA.end()) {
    // updating settings map

    /// do no bound check if both bounds are equal to zero
    if (!(fSettingMapFPGA[name].lowerBound == 0 &&
          fSettingMapFPGA[name].upperBound == 0)) {
      /// check bounds
      if (newVal > fSettingMapFPGA[name].upperBound ||
          newVal < fSettingMapFPGA[name].lowerBound) {
        std::cerr << "ERROR: Value of user setting <" << name
                  << "> is out bounds specified in " << fDefintionFileFPGA
                  << std::endl;
        return TC_ERR_CONF_FAILURE;
      }
    }
    // update the setting
    fSettingMapFPGA[name].value = newVal;
    Setting setting = fSettingMapFPGA[name];
    // update the register value
    std::map<uint32_t, RegisterFPGA>::iterator itReg;
    itReg = fRegisterMapFPGA.find(setting.regAddr);
    uint32_t val = 0;
    if (itReg != fRegisterMapFPGA.end()) {
      val = fRegisterMapFPGA[setting.regAddr].val;
    }
    // checking if we have to set the full register
    if (setting.nBits == 0x20 && setting.startBit == 0) {
      val = setting.value;
    } else {  // Filling the register partially
      ModifyRegisterPartially(val, setting);
    }
    // update
    fRegisterMapFPGA[setting.regAddr].val = val;
  } else {
    std::cerr << "ERROR: undefined setting name in FPGA definition file: "
              << name << std::endl;
    return TC_ERR_CONF_FAILURE;
  }
  return TC_OK;
}

int RegisterSettings::GetFPGARegisterValue(uint32_t addr, uint32_t& val) const {
  RF_cit cit = fRegisterMapFPGA.find(addr);
  if (cit != fRegisterMapFPGA.end()) {
    val = cit->second.val;
  } else {
    std::cerr << "ERROR: Unknown register address <" << addr << ">"
              << std::endl;
    return TC_ERR_CONF_FAILURE;
  }

  return TC_OK;
}

int RegisterSettings::GetTriggerASICRegisterValue(const std::string& name,
                                                  uint8_t asic,
                                                  uint16_t& val) const {
  return GetASICRegisterValue(name, asic, val);
}
int RegisterSettings::GetASICRegisterValue(const std::string& name,
                                           uint8_t asic, uint16_t& val,
                                           bool isTriggerASIC) const {
  if (asic > 3) {
    std::cerr << "ERROR, GetASICRegisterValue called with an ASIC > 3 "
              << std::endl;
    return TC_ERR_CONF_FAILURE;
  }

  uint8_t address;
  GetASICSettingRegisterAddress(name, address, isTriggerASIC);

  if (!isTriggerASIC) {
    RA_cit cit = fRegisterMapASIC.find(address);
    if (cit != fRegisterMapASIC.end()) {
      val = static_cast<uint16_t>(cit->second.val[asic]);
    } else {
      std::cerr << "ERROR: Unknown register addres 0x" << int(address) << ">"
                << std::endl;
      return TC_ERR_CONF_FAILURE;
    }
  } else {
    RA_cit cit = fRegisterMapTriggerASIC.find(address);
    if (cit != fRegisterMapTriggerASIC.end()) {
      val = static_cast<uint16_t>(cit->second.val[asic]);
    } else {
      std::cerr << "ERROR: Unknown register addres 0x" << int(address) << ">"
                << std::endl;
      return TC_ERR_CONF_FAILURE;
    }
  }
  return TC_OK;
}

int RegisterSettings::GetFPGASettingRegisterAddress(const std::string& name,
                                                    uint32_t& addr) const {
  SF_cit cit = fSettingMapFPGA.find(name);
  if (cit != fSettingMapFPGA.end()) {
    addr = cit->second.regAddr;
  } else {
    std::cerr << "ERROR: Unknown settings <" << name << ">" << std::endl;
    return TC_ERR_CONF_FAILURE;
  }
  return TC_OK;
}

int RegisterSettings::GetTriggerASICSettingRegisterAddress(
    const std::string& name, uint8_t& addr) const {
  return GetASICSettingRegisterAddress(name, addr, true);
}

int RegisterSettings::GetASICSettingRegisterAddress(const std::string& name,
                                                    uint8_t& addr,
                                                    bool isTriggerASIC) const {
  if (!isTriggerASIC) {
    SA_cit cit = fSettingMapASIC.find(name);
    if (cit != fSettingMapASIC.end()) {
      addr = static_cast<uint8_t>(cit->second.settingASIC[0].regAddr);
    } else {
      std::cerr << "ERROR: Unknown settings <" << name << ">" << std::endl;
      return TC_ERR_CONF_FAILURE;
    }
  } else {
    SA_cit cit = fSettingMapTriggerASIC.find(name);
    if (cit != fSettingMapTriggerASIC.end()) {
      addr = static_cast<uint8_t>(cit->second.settingASIC[0].regAddr);
    } else {
      std::cerr << "ERROR: Unknown settings <" << name << ">" << std::endl;
      return TC_ERR_CONF_FAILURE;
    }
  }
  return TC_OK;
}

void RegisterSettings::PrintSetting(Setting set) const {
  std::cout << std::hex << "regAddr: 0x" << set.regAddr << "\n";
  std::cout << std::hex << "nBits: 0x" << set.nBits << "(hex), " << std::dec
            << set.nBits << "(dec)\n";
  std::cout << std::hex << "startBit: 0x" << set.startBit << "\n";
  std::cout << std::hex << "value: 0x" << set.value << "\n";
  //  std::cout << std::hex << "access: 0x" << set.access << "\n";
  std::cout << std::hex << "lowerBound: 0x" << set.lowerBound << "\n";
  std::cout << std::hex << "upperBound: 0x" << set.upperBound << "\n";
  std::cout << std::dec << "multiplier: " << set.multiplier << "\n";
  std::cout << std::dec << "offset: " << set.offset << "\n";
  std::cout << "description: " << set.description << std::endl;
}

void RegisterSettings::PrintFPGASetting(const std::string& settingName) const {
  SF_cit cit = fSettingMapFPGA.find(settingName);
  if (cit != fSettingMapFPGA.end()) {
    std::cout << "FPGA Settings Name: " << settingName << "\n";
    PrintSetting(cit->second);
  } else {
    std::cerr << "WARNING: Unknown name of settings: " << settingName
              << std::endl;
  }
}

void RegisterSettings::PrintTriggerASICSetting(
    const std::string& settingName) const {
  PrintASICSetting(settingName, true);
}

void RegisterSettings::PrintASICSetting(const std::string& settingName,
                                        bool isTriggerASIC) const {
  if (!isTriggerASIC) {
    SA_cit cit = fSettingMapASIC.find(settingName);
    if (cit != fSettingMapASIC.end()) {
      std::cout << "ASIC Settings Name: " << settingName << "\n";
      for (int i = 0; i < 4; ++i) {
        std::cout << "ASIC " << i << "\n";
        PrintSetting(cit->second.settingASIC[i]);
      }
    } else {
      std::cerr << "WARNING: Unknown name of settings: " << settingName
                << std::endl;
    }
  } else {
    SA_cit cit = fSettingMapTriggerASIC.find(settingName);
    if (cit != fSettingMapTriggerASIC.end()) {
      std::cout << "ASIC Settings Name: " << settingName << "\n";
      for (int i = 0; i < 4; ++i) {
        std::cout << "ASIC " << i << "\n";
        PrintSetting(cit->second.settingASIC[i]);
      }
    } else {
      std::cerr << "WARNING: Unknown name of settings: " << settingName
                << std::endl;
    }
  }
}

void RegisterSettings::PrintAllSettings() const {
  std::cout << "\n------FPGA SETTINGS -----\n" << std::endl;
  PrintHeaderFPGA();
  for (SF_cit cit = fSettingMapFPGA.cbegin(); cit != fSettingMapFPGA.cend();
       ++cit) {
    PrintFPGASetting(cit->first);
  }
  std::cout << "\n------ASIC SETTINGS -----\n" << std::endl;
  PrintHeaderASIC();
  for (SA_cit cit = fSettingMapASIC.cbegin(); cit != fSettingMapASIC.end();
       ++cit) {
    PrintASICSetting(cit->first);
  }

  if (fDefintionFileTriggerASIC != "")
    std::cout << "\n------TRIGGER ASIC SETTINGS -----\n" << std::endl;
  PrintHeaderTriggerASIC();
  for (SA_cit cit = fSettingMapTriggerASIC.cbegin();
       cit != fSettingMapTriggerASIC.end(); ++cit) {
    PrintASICSetting(cit->first, true);
  }
}

void RegisterSettings::PrintAllRegisters() const {
  std::cout << "\n Registers FPGA " << std::endl;
  for (auto it = fRegisterMapFPGA.begin(); it != fRegisterMapFPGA.end(); it++) {
    std::cout << std::hex << "0x" << int(it->first) << ":\t0x" << it->second.val
              << std::endl;
  }

  std::cout << "\n ASIC " << std::endl;
  for (auto it = fRegisterMapASIC.begin(); it != fRegisterMapASIC.end(); it++) {
    std::cout << std::hex << "0x" << int(it->first) << ":\t0x"
              << it->second.val[0] << "\t 0x" << it->second.val[1] << "\t 0x"
              << it->second.val[2] << "\t0x" << it->second.val[3] << std::endl;
  }

  if (fDefintionFileTriggerASIC != "") {
    std::cout << "\n TRIGGER ASIC " << std::endl;
    for (auto it = fRegisterMapTriggerASIC.begin();
         it != fRegisterMapTriggerASIC.end(); it++) {
      std::cout << std::hex << "0x" << int(it->first) << ":\t0x"
                << it->second.val[0] << "\t 0x" << it->second.val[1] << "\t 0x"
                << it->second.val[2] << "\t0x" << it->second.val[3]
                << std::endl;
    }
  }
}

void RegisterSettings::PrintHeaderFPGA() const {
  std::cout << "HEADER FPGA\n";
  std::cout << "TM_FIRMWARE_VERSION: " << std::hex << fFPGAFirmwareVersion
            << "\n";
  std::cout << "DESCRIPTION: " << fFPGADescription << "\n";
  std::cout << "RESPONSIBLE_AUTHOR: " << fFPGAAuthor << "\n";
  std::cout << "NUM_REGISTERS: " << fFPGANumberOfRegisters << std::endl;
}

void RegisterSettings::PrintHeaderTriggerASIC() const { PrintHeaderASIC(true); }

void RegisterSettings::PrintHeaderASIC(bool isTriggerASIC) const {
  std::cout << "HEADER ASIC"
            << "\n";
  if (!isTriggerASIC) {
    std::cout << "DESCRIPTION: " << fASICDescription << "\n";
    std::cout << "RESPONSIBLE_AUTHOR: " << fASICAuthor << "\n";
    std::cout << "NUM_REGISTERS: " << fASICNumberOfRegisters << std::endl;
  } else {
    std::cout << "DESCRIPTION: " << fTriggerASICDescription << "\n";
    std::cout << "RESPONSIBLE_AUTHOR: " << fTriggerASICAuthor << "\n";
    std::cout << "NUM_REGISTERS: " << fTriggerASICNumberOfRegisters
              << std::endl;
  }
}

void RegisterSettings::GenerateTriggerASICMarkdown(
    const std::string& fname) const {
  GenerateASICMarkdown(fname, true);
}
void RegisterSettings::GenerateASICMarkdown(const std::string& fname,
                                            bool isTriggerASIC) const {
  std::map<uint32_t, std::string> sorted;
  typedef std::map<uint32_t, std::string>::const_iterator s_cit;
  if (!isTriggerASIC) {
    for (SA_cit cit = fSettingMapASIC.cbegin(); cit != fSettingMapASIC.cend();
         ++cit) {
      sorted[cit->second.settingASIC[0].regAddr * 100 + 32 -
             cit->second.settingASIC[0].startBit] = cit->first;
    }
  } else {
    for (SA_cit cit = fSettingMapTriggerASIC.cbegin();
         cit != fSettingMapTriggerASIC.cend(); ++cit) {
      sorted[cit->second.settingASIC[0].regAddr * 100 + 32 -
             cit->second.settingASIC[0].startBit] = cit->first;
    }
  }

  std::ofstream fout;
  fout.open(fname.c_str());

  fout << "Register Map of a TARGET ASIC: " << fDefintionFileASIC << "\n";
  fout << "============\n";

  //  fout << "|Register|Name|Bit Range|Default|Read Only|Description|\n";
  fout << "|Register|Name|Bit Range|Default|Access   |Description|\n";
  fout << "|--------|----|---------|-------|---------|-----------|\n";

  uint32_t previous_reg = std::numeric_limits<uint32_t>::max();
  for (s_cit cit = sorted.cbegin(); cit != sorted.cend(); ++cit) {
    std::string name = cit->second;
    Setting setting;
    if (!isTriggerASIC) {
      setting = fSettingMapASIC.at(name).settingASIC[0];
    } else {
      setting = fSettingMapTriggerASIC.at(name).settingASIC[0];
    }

    uint32_t reg = cit->first / 100;
    if (reg != previous_reg) {
      fout << "|0x" << std::setfill('0') << std::setw(2) << std::hex
           << std::uppercase << reg << "|";
      previous_reg = reg;
    } else {
      fout << "||";
    }
    fout << "`" << name << "`|";
    fout << std::dec;
    if (setting.nBits == 1) {
      fout << setting.startBit << "|";
    } else {
      fout << setting.startBit + setting.nBits - 1 << "--" << setting.startBit
           << "|";
    }
    fout << "0x" << std::setfill('0') << std::setw(3) << std::hex
         << std::uppercase << setting.value << "|";
    //    fout << (setting.isReadOnly ? "Yes" : "No") << "|";
    if (setting.access == eRW) {
      fout << "Read/Write"
           << "|";
    } else if (setting.access == eR) {
      fout << "Read"
           << "|";
    } else if (setting.access == eW) {
      fout << "Write"
           << "|";
    } else {
      fout << "???"
           << "|";
    }
    //    fout << (setting.isReadOnly ? "Yes" : "No") << "|";
    fout << setting.description << "|\n";
  }

  fout.close();
}

void RegisterSettings::GenerateFPGAMarkdown(const std::string& fname) const {
  std::map<uint32_t, std::string> sorted;
  std::map<std::string, Setting>::const_iterator cit;
  for (cit = fSettingMapFPGA.cbegin(); cit != fSettingMapFPGA.cend(); ++cit) {
    sorted[cit->second.regAddr * 100 + 32 - cit->second.startBit] = cit->first;
  }

  std::ofstream fout;
  fout.open(fname.c_str());

  fout << "Register Map of a TARGET FPGA: " << fDefintionFileFPGA << "\n";
  fout << "============\n";
  fout << "|Register|Name|Bit Range|Default|Read Only|Description|\n";
  fout << "|--------|----|---------|-------|---------|-----------|\n";

  std::map<uint32_t, std::string>::const_iterator cit2;
  uint32_t previous_reg = std::numeric_limits<uint32_t>::max();
  for (cit2 = sorted.cbegin(); cit2 != sorted.cend(); ++cit2) {
    std::string name = cit2->second;
    Setting setting = fSettingMapFPGA.at(name);
    uint32_t reg = cit2->first / 100;
    if (reg != previous_reg) {
      fout << "|0x" << std::setfill('0') << std::setw(2) << std::hex
           << std::uppercase << reg << "|";
      previous_reg = reg;
    } else {
      fout << "||";
    }
    fout << "`" << name << "`|";
    fout << std::dec;
    if (setting.nBits == 1) {
      fout << setting.startBit << "|";
    } else {
      fout << setting.startBit + setting.nBits - 1 << "--" << setting.startBit
           << "|";
    }
    fout << "0x" << std::setfill('0') << std::setw(3) << std::hex
         << std::uppercase << setting.value << "|";
    //    fout << (setting.isReadOnly ? "Yes" : "No") << "|";
    if (setting.access == eRW) {
      fout << "Read/Write"
           << "|";
    } else if (setting.access == eR) {
      fout << "Read"
           << "|";
    } else if (setting.access == eW) {
      fout << "Write"
           << "|";
    } else {
      fout << "???"
           << "|";
    }
    fout << setting.description << "|\n";
  }
  fout.close();
}

}  // namespace TargetDriver
}  // namespace CTA
