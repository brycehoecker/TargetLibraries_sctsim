// Copyright (c) 2015 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Provides the interface for Firmware/ASIC definition and config files
 */
#ifndef INCLUDE_TARGETDRIVER_REGISTERSETTINGS_H_
#define INCLUDE_TARGETDRIVER_REGISTERSETTINGS_H_

#include <iostream>
#include <map>
#include <string>

namespace CTA {
namespace TargetDriver {
/// Accessing mode for setting, eRW = Read and Write, eR = Read Only, eW = Write
/// Only (do not check return value),eRW_NS = Read/Write, but non sticky write,
/// so do not read back after a write
enum Access { eRW, eR, eW, eRW_NS };

struct Setting {
  uint32_t regAddr;
  // TODO(Akira): Change them to uint8_t, but be carefule when converting
  // stringstream to uint8_t values
  uint16_t nBits;
  uint16_t startBit;
  uint32_t value;
  //  bool isReadOnly;
  Access access;
  uint32_t lowerBound;
  uint32_t upperBound;
  float multiplier;
  float offset;
  std::string description;
};

struct SettingASIC {
  Setting settingASIC[4];
};

struct RegisterFPGA {
  uint32_t val;
  //  bool isReadOnly;
  Access access;
};

struct RegisterASIC {
  uint16_t val[4];
};

/*!
 * @class RegisterSettings
 * @brief A class to hold all the register values for FPGA and ASIC on target
 *modules
 *
 */
class RegisterSettings {
 public:
  /// Default constructor needs as arguments a FPGA and\n
  /// the TargetASIC definition file
  RegisterSettings(const std::string& targetFPGADefinitionFile,
                   const std::string& targetASICDefinitionFile);
  /// Constructor when we have a trigger and sampling ASIC
  RegisterSettings(const std::string& targetFPGADefinitionFile,
                   const std::string& targetASICDefinitionFile,
                   const std::string& targetTriggerASICDefinitionFile);
  /// Prints an FPGA Setting to the standard output
  void PrintSetting(Setting set) const;
  /// Prints an FPGA Setting to the standard output
  void PrintFPGASetting(const std::string& settingName) const;
  void PrintASICSetting(const std::string& settingName,
                        bool isTriggerASIC = false) const;
  void PrintTriggerASICSetting(const std::string& settingName) const;
  void PrintAllSettings() const;
  void PrintHeaderFPGA() const;
  void PrintHeaderASIC(bool isTriggerASIC = false) const;
  void PrintHeaderTriggerASIC() const;

  void PrintAllRegisters() const;

  /// Generates a markdown file for documentation of ASIC registers
  void GenerateASICMarkdown(const std::string& fname,
                            bool isTriggerASIC = false) const;
  /// Generates a markdown file for documentation of ASIC registers
  void GenerateTriggerASICMarkdown(const std::string& fname) const;

  /// Generates a markdown file for documentation of FPGA registers
  void GenerateFPGAMarkdown(const std::string& fname) const;

  int ReadUserFPGAConfigFile(const std::string& configFile);
  int ReadUserTriggerASICConfigFile(const std::string& configFile);
  int ReadUserASICConfigFile(const std::string& configFile,
                             bool isTriggerASIC = false);
  // Modify the value of a setting
  int ModifyFPGASetting(const std::string& name, uint32_t newVal);
  void GetRegisterPartially(uint32_t reg, Setting set,
                            uint32_t& reg_par);  // NOLINT(runtime/references)

  int ModifyTriggerASICSetting(const std::string& name, uint8_t asic,
                               uint16_t val);
  int ModifyASICSetting(const std::string& name, uint8_t asic, uint16_t val,
                        bool isTriggerASIC = false);  /// HARM:DONE

  int GetFPGARegisterValue(uint32_t addr,
                           uint32_t& val) const;  // NOLINT(runtime/references)
  int GetTriggerASICRegisterValue(
      const std::string& name, uint8_t asic,
      uint16_t& val) const;  // NOLINT(runtime/references)

  int GetASICRegisterValue(
      const std::string& name, uint8_t asic, uint16_t& val,
      bool isTriggerASIC = false) const;  // NOLINT(runtime/references)
  int GetFPGASettingRegisterAddress(
      const std::string& name,
      uint32_t& addr) const;  // NOLINT(runtime/references)

  int GetTriggerASICSettingRegisterAddress(
      const std::string& name,
      uint8_t& addr) const;  // NOLINT(runtime/references)
  int GetASICSettingRegisterAddress(
      const std::string& name, uint8_t& addr,
      bool isTriggerASIC = false) const;  // NOLINT(runtime/references)

  std::string fType;
  uint32_t fFPGAFirmwareVersion;
  std::string fFPGADescription;
  std::string fFPGAAuthor;
  uint32_t fFPGANumberOfRegisters;

  std::string fASICDescription;
  std::string fASICAuthor;
  uint32_t fASICNumberOfRegisters;
  std::string fTriggerASICDescription;
  std::string fTriggerASICAuthor;
  uint32_t fTriggerASICNumberOfRegisters;

  int CheckFPGARegisterConsistency();
  int CheckTriggerASICRegisterConsistency();
  int CheckASICRegisterConsistency(bool isTriggerASIC = false);  /// HARM:DONE

  int ReadDefinitionFileFPGA();
  int ReadDefinitionFileTriggerASIC();
  int ReadDefinitionFileASIC(bool isTriggerASIC = false);

  // Helper code to modify parts of a 32 bit register
  void ModifyRegisterPartially(uint32_t& reg,  // NOLINT(runtime/references)
                               Setting set);
  bool CheckRegisterPartially(uint32_t reg, Setting set);
  // Add settings and updates register map accordingly
  int AddFPGASetting(const std::string& name, Setting setting);
  int AddTriggerASICSetting(const std::string& name, SettingASIC setting);
  int AddASICSetting(const std::string& name, SettingASIC setting,
                     bool isTriggerASIC = false);
  int UpdateFPGASettingMapFromRegisterMap();

  const std::string fDefintionFileFPGA;
  const std::string fDefintionFileASIC;
  const std::string fDefintionFileTriggerASIC;
  std::map<std::string, Setting> fSettingMapFPGA;
  typedef std::map<std::string, Setting>::const_iterator SF_cit;
  /// settings for the sampling asic (or sampling and triggering T5/T7)
  std::map<std::string, SettingASIC> fSettingMapASIC;
  typedef std::map<std::string, SettingASIC>::const_iterator SA_cit;
  /// Trigger ASIC settings map
  std::map<std::string, SettingASIC> fSettingMapTriggerASIC;

  std::map<uint32_t, RegisterFPGA> fRegisterMapFPGA;
  typedef std::map<uint32_t, RegisterFPGA>::const_iterator RF_cit;
  std::map<uint8_t, RegisterASIC> fRegisterMapASIC;
  typedef std::map<uint8_t, RegisterASIC>::const_iterator RA_cit;
  /// Trigger ASIC
  std::map<uint8_t, RegisterASIC> fRegisterMapTriggerASIC;
};

}  // namespace TargetDriver
}  // namespace CTA

#endif  // INCLUDE_TARGETDRIVER_REGISTERSETTINGS_H_
