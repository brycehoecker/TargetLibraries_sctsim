// Copyright (c) 2015 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains the generic interface for all target modules
 */
#ifndef INCLUDE_TARGETDRIVER_TARGETMODULE_H_
#define INCLUDE_TARGETDRIVER_TARGETMODULE_H_

#include <unistd.h>
#include <iostream>
#include <string>

#include "TargetDriver/RegisterSettings.h"
#include "TargetDriver/UDPClient.h"

// Defaults and port number definitions
// CLIENT PORTS
// clang-format off
#define TM_SOURCE_PORT   8200  ///< Arbitary: +0-31 port from which we send TM commands and to which the responses come
#define TM_DAQ_PORT      8107  ///< Arbitary: port to which data is sent from TM
#define TM_SPECIAL_PORT  8300  ///< Reserve for special test purposes - e.g. Exists()

// SERVER PORTS
#define TM_DEST_PORT     8105  /// Default port which the TMs listen for commands
#define TM_DATASEND_PORT 8106  /// Arbitrary - used for simulator

#define TM_SOCK_BUF_SIZE_SC   10000  /// Default socket buffer size for slow control
#define TM_SOCK_BUF_SIZE_DAQ 999424  /// Default socket buffer size for DAQ -- should be same on PC, see
                                     /// proc/sys/net/core/rmem_max for the max allowed value (often 124928)
#define TM_MAX_ATTEMPTS 4  ///< Default number of maximum attemps for register operations (read/write)
#define TM_RESPONSE_TIME_OUT  20  /// Default number of ms for receive time out
#define TM_DAQ_TIME_OUT      100  /// Default number of milliseconds -- how long does the poll in GetDataPacket wait before giving up
#define TM_CONTROLPACKET_SIZE 16
#define TM_BUFFER_SIZE 4095

#define TM_ASICS                   4
#define TM_TRIGGERPIXELS_PER_ASIC  4
#define TM_PIXELS_PER_ASIC        16
#define TM_TRIGGERPIXELS_PER_MODULE (TM_ASICS * TM_TRIGGERPIXELS_PER_ASIC)
#define TM_PIXELS_PER_MODULE        (TM_ASICS * TM_PIXELS_PER_ASIC)

// States
#define TM_STATE_NOTPRESENT   -3  // For use with Backplane
#define TM_STATE_NOTPOWERED   -2  // For use with Backplane
#define TM_STATE_UNRESPONSIVE -1  // Contact lost / problematic
#define TM_STATE_UNDEFINED     0  // Uncontacted
#define TM_STATE_SAFE          1  // Registers have default values - ASIC power is off
#define TM_STATE_PRESYNC       2  // ASIC power on and software reset done, sampling off - ready to be synced
#define TM_STATE_READY         3  // Sampling on, synced.
// clang-format on

namespace CTA {
namespace TargetDriver {

/*!
 * @class TargetModule
 * @brief A single class to use for communicating with all versions of the
 *Target module, register behaviour is defined in a text file
 *
 */
class TargetModule : public UDPClient {
  enum ModuleType {
    kT5Module,
    kT7Module,
    kT7ModuleBP,
    kTCEval,
    kTCT5TEAEval,
    kTCModule,
    kTCModuleBP,
    kNonTM
  };

 public:
  /// used to generate a target module without initialising the Settings Map.
  explicit TargetModule(uint16_t pModuleId = 1);
  /// Default target module constructor. Specify full path to FPGA/ASIC
  /// definition files
  TargetModule(const std::string& pFPGADef, const std::string& pASICDef,
               uint16_t pModuleId = 1);
  /// Default target module constructor. Specify full path to FPGA/ASIC
  /// definition files
  TargetModule(const std::string& pFPGADef, const std::string& pASICDef,
               const std::string& pTriggerASICDef, uint16_t pModuleId = 1);

  // Set the IP address for client and module - for later use by GotoSafe()
  void SetIPAddresses(const std::string& pClientIP,
                      const std::string& pModuleIP);
  void SetClientIP(const std::string& pClientIP) { fClientIP = pClientIP; }
  void SetModuleIP(const std::string& pModuleIP) { fModuleIP = pModuleIP; }

  bool Exists(std::string ipaddress, std::string myip);

  /*! Enable the two way slow control communication with a Target Module with
   *IP\n
   *pModuleIP from pClientIP. tm_number should be unique as it determines the
   *port number that will be used - e.g. 0-31 for a camera*/
  int Connect();  // must set IP addresses first
  /*! wrapper around Connect() for backward compatibility */
  int EstablishSlowControlLink(const std::string& pClientIP,
                               const std::string& pModuelIP);

  /// Wrapper around UDPClient::AddDataListener - listen for data arriving at IP
  /// address pPCIP
  int AddDAQListener(const std::string& pClientIP);

  /*! Prepare a control packet based on addr and data and the flag
   *   iswrite\n
   *   (true if this is a write register command)\n
   *   Format:
   *\code----------------------------------
   *|31|30|29|...|24|23|...|4|3|2|1|0|
   *|            header              |
   *| 0| W| 0|...| 0| address[23:0]  |
   *|          Data[31:0]            |
   *|            footer              |
   *----------------------------------\endcode
   */
  static void PackControlPacket(uint8_t* packet, uint32_t addr, uint32_t data,
                                bool iswrite);
  /// Extract the address, data and iswrite flag from a slow control packet
  static int UnpackControlPacket(const uint8_t* packet,
                                 uint32_t& addr,  // NOLINT(runtime/references)
                                 uint32_t& data,  // NOLINT(runtime/references)
                                 bool& iswrite);  // NOLINT(runtime/references)

  /// Get the firmware version of the FPGA
  int GetFirmwareVersion(uint32_t& fw_version) {  // NOLINT(runtime/references)
    if (fVerbose) std::cout << "Checking firmware version" << std::endl;
    int stat = ReadRegister(0x00, fw_version);
    if (fVerbose) std::cout << "Got " << fw_version << " " << stat << std::endl;
    return stat;
  }
  /// Get the primary board identifier/SN
  int GetPrimaryBoardID(uint64_t& pbid);

  /// Check that the response packet from the TM is OK
  static int CheckResponse(const uint8_t* packet);
  /// returns the phase of the comms clock
  int GetClockPhase() const { return fClockPhase; }

  // Sends the "SoftwareReset" command which halts the signal sampling and
  // prepares the module for a SYNC message from the backplane
  void StopSampling();

  // Checks that the TM register contents are consistent with the locally stored
  // settings list values
  int CheckRegisters();

  // State Transitions
  int GoToSafe();
  int GoToPreSync();
  int GoToReady();

  bool IsReady() const { return fState == TM_STATE_READY; }
  bool IsPreSync() const { return fState == TM_STATE_PRESYNC; }
  bool IsSafe() const { return fState == TM_STATE_SAFE; }
  bool IsUndefined() const { return fState == TM_STATE_UNDEFINED; }
  bool IsContactable() const { return fState > 0; }
  bool IsUnresponsive() const { return fState == TM_STATE_UNRESPONSIVE; }

  int GetState() const { return fState; }

  int ReconnectToServer(const std::string& pMyIP, uint16_t pMySourcePort,
                        const std::string& pServerIP, uint16_t pServerPort,
                        int32_t pSocketBufferSize = -1);
  void PrintAllRegisterSettings() { fTargetSettings.PrintAllSettings(); };

  void PrintAllRegisterValues() { fTargetSettings.PrintAllRegisters(); }

  std::string GetStateString() {
    switch (fState) {
      case TM_STATE_NOTPRESENT:
        return ("Not Present");
      case TM_STATE_NOTPOWERED:
        return ("Not Powered");
      case TM_STATE_UNRESPONSIVE:
        return ("Not Responding");
      case TM_STATE_UNDEFINED:
        return ("Not yet contacted");
      case TM_STATE_SAFE:
        return ("Safe");
      case TM_STATE_PRESYNC:
        return ("Pre-sync");
      case TM_STATE_READY:
        return ("Ready");
    }
    return ("Should not happen - fix code");
  }

 protected:
  RegisterSettings fTargetSettings;         //< (Register) Settings for this TM
                                            /// HARM: MOVE BACK UP....
  RegisterSettings fTargetSettingsDefault;  //< store the default values from
                                            // the definition file and is called
                                            // in GoToSafe
  uint16_t fModuleId;                       //< Module Id;
  int fClockPhase;                          //< Phase of the comms clock
  int fState;                               //< Internal State
  /// Used by WriteRegister and ReadRegister to make fMaxAttempts to send a
  /// command packet to the Target Module
  int RegisterOperation(uint32_t address,
                        uint32_t& data,  // NOLINT(runtime/references)
                        bool iswrite, bool onlySend = false);

  ModuleType fModuleType;

  std::string fClientIP;
  std::string fModuleIP;

  std::string GetStateString() const {
    switch (fState) {
      case TM_STATE_NOTPRESENT:
        return ("Not Present");
      case TM_STATE_NOTPOWERED:
        return ("Not Powered");
      case TM_STATE_UNRESPONSIVE:
        return ("Unresponsive");
      case TM_STATE_UNDEFINED:
        return ("Uncontacted");
      case TM_STATE_SAFE:
        return ("Safe");
      case TM_STATE_PRESYNC:
        return ("Presync");
      case TM_STATE_READY:
        return ("Ready");
    }
    return ("Should never occur - fix code");
  }

 private:
  uint8_t fBuffer[TM_CONTROLPACKET_SIZE];  //< buffer for use in receiving slow
                                           // control packets from the TM

 public:
  /// Direct write access to target module (discouraged to use directly since
  /// fTargetSettings doesn't get updated)
  int WriteRegister(uint32_t address, uint32_t data) {
    return RegisterOperation(address, data, true);
  }
  /// Write and reads back the information and checks consistency (discouraged
  /// to use directly since fTargetSettings doesn't get updated)
  int WriteRegisterAndCheck(uint32_t address, uint32_t data);

  /// Write a register onthe target module (discouraged to use directly since
  /// fTargetSettings doesn't get updated)
  int WriteTARGETRegister(bool enableAsic0, bool enableAsic1, bool enableAsic2,
                          bool enableAsic3, bool readback, bool latchIsRequired,
                          uint8_t address, uint16_t value,
                          bool isTriggerASIC = false);
  /// Write to all ASIC register directly (discouraged to use directly since
  /// fTargetSettings doesn't get updated)
  int WriteTARGETRegister(bool readback, bool latchIsRequired, uint8_t address,
                          uint16_t value, bool isTriggerASIC = false) {
    return WriteTARGETRegister(true, true, true, true, readback,
                               latchIsRequired, address, value, isTriggerASIC);
  }

  /// Write new setting to target module and update\n
  /// the fTargetSettings accodingly\n
  /// This is the only method that is provided to the\n
  /// user to write values to TargetModule after\n
  /// initialization.
  int WriteSetting(const std::string& name, uint32_t val);
  /// Read back the value of a setting from the target module
  int ReadSetting(const std::string& name,
                  uint32_t& val);  // NOLINT(runtime/references)

  /// Use to write default values from definition file
  int WriteSettingFromConfig(const std::string& name);

  /// Write register stored in fTargetSettings
  /// Should only be used during initialization
  int WriteRegisterFromConfig(uint32_t address);
  ///
  /// Write ASIC setting to taget module
  int WriteASICSetting(const std::string& name, uint8_t asic, uint16_t val,
                       bool individualASIC = false, bool isTriggerASIC = false);
  int WriteTriggerASICSetting(const std::string& name, uint8_t asic,
                              uint16_t val, bool individualASIC = false) {
    return WriteASICSetting(name, asic, val, individualASIC, true);
  }

  ///
  /// Write ASIC register using the addres of the register from fTagetSettings
  int WriteASICRegisterFromConfig(uint8_t address, uint8_t asic = 0,
                                  bool individualASIC = false,
                                  bool isTriggerASIC = false);
  int WriteTriggerASICRegisterFromConfig(uint8_t address, uint8_t asic = 0,
                                         bool individualASIC = false) {
    return WriteASICRegisterFromConfig(address, asic, individualASIC, true);
  }

  /// Write ASIC setting using the setting from fTagetSettings
  int WriteASICSettingFromConfig(const std::string& name, uint8_t asic = 0,
                                 bool individualASIC = false,
                                 bool isTriggerASIC = false);
  int WriteTriggerASICSettingFromConfig(const std::string& name,
                                        uint8_t asic = 0,
                                        bool individualASIC = false) {
    return WriteASICSettingFromConfig(name, asic, individualASIC, true);
  }

  ///
  /// Write a setting into the FPGA using the calibration\n
  /// constants in the definition file
  int WriteSettingCalibrated(const std::string& name, float val);

  ///
  /// Reads a FPGA setting an gives back the calibrated value using the
  /// calibration\n
  /// constants in the definition file
  int ReadSettingCalibrated(const std::string& name,
                            float& val);  // NOLINT(runtime/references)

  ///
  /// Write a setting into the ASIC using the calibration\n
  /// constants in the definition file
  int WriteSettingASICCalibrated(const std::string& name, uint8_t asic,
                                 float val, bool individualASIC = false,
                                 bool isTriggerASIC = false);
  int WriteSettingTriggerASICCalibrated(const std::string& name, uint8_t asic,
                                        float val,
                                        bool individualASIC = false) {
    return WriteSettingASICCalibrated(name, asic, val, individualASIC, true);
  }

  /// Function to power up the AICS one-by-one or all together
  int PowerUpASIC(uint8_t asic = 0,
                  bool individialASIC = 0);  // power up one or all ASICs
  /// The initialise functions puts the target modules in a defined state.\n
  /// It powers up the asic and sequentially write the default values to\n
  /// the ASIC registers.
  /// Afterwards it is put into a state ready for data taking, DLL feedback is
  /// not enabled
  int Initialise();

  ///
  /// Enable the DLL feedback, for BP or testerboard versions  this\n
  /// needs to be called after syncing and starting timebase. Only for T7 and TC
  /// ASICs \n
  /// Is called in  GoToReady when using a BP
  int EnableDLLFeedback();

  ///
  /// Disable the DLL Feedback
  /// needs to be disabled before a software reset
  int DisableDLLFeedBack();

  /// Reads a register on the TARGET Module FPGA - makes fMaxAttempts attempts
  /// ------
  /// could add higher level functions which try multiple times to read or write
  int ReadRegister(uint32_t address,
                   uint32_t& data) {  // NOLINT(runtime/references)
    return RegisterOperation(address, data, false);
  }
  ///
  /// Fill the register map from the FPGA on the module. Use when module is
  /// already  initialised.
  int FillRegisterMapFromFPGA();

  ///
  /// Writes the value in data to address on a Target Module - makes
  /// fMaxAttempts attempts
  ///
  /// Writes a Target Register and reads the value back and compares them.
  /// Returns true if values are the same

  ///**********************************
  /// Pings the data port to avoid firewall problems A.K.A "the akira hack"
  static void DataPortPing(const std::string& pClientIP,
                           const std::string& pModuelIP);

  void
  DataPortPing();  // same - but using internal values for client and module IP

  // We need this at the moment for T7Module, because the old firmware only has
  // one port for
  // Slow Control and Data
  void DeleteDAQListeners();

  void QueryAndPrintAllRegisters(
      std::ostream& stream);  // NOLINT(runtime/references)

  //////////////////////
  /// I2C fuctions     //
  //////////////////////

  ///
  /// helper function for i2c commands on power board
  /// only for the power board, since other boards have only i2c device
  enum eI2CAddress {
    eHVInput = 111,     // 0b1101111;
    eTemperature = 72,  // 0b1001000;
    eID = 80,           // 0b1010000;
    eHVEnable = 33,     // 0b0100001;
    eHVSetDAC0 = 32,    // 0b0100000;
    eHVSetDAC1 = 47,    // 0b0101111;
    eHVSetDAC2 = 44,    // 0b0101100;
    eHVSetDAC3 = 35,    // 0b0100011;
    eUnkown = 0
  };
  /// Read the HV current input to the module in Ampere
  int ReadHVCurrentInput(float& val /*A*/);  // done

  ///
  /// Read the HV Voltage input to the module in Volt
  int ReadHVVoltageInput(float& val /*V*/);  // done

  ///
  /// Temperature sensore in Power Board
  int GetTempI2CPower(float& val);  // done

  ///
  /// Temperature Aux Board
  int GetTempI2CAux(float& val);  // done

  ///
  /// Temperature Primary Board
  int GetTempI2CPrimary(float& val);  // done

  ///
  /// Temperature SiPM
  int GetTempSIPM(float& val);  // done and tested

  ///
  /// read the serial ID from the Maxim DS28CM00 serial id chip
  int ReadPowerBoardID(uint64_t& val);  // done

  ///
  /// Reads the two byte mask for enabling HV on the 16 super pixel channels
  int ReadHVEnableBytes(uint8_t& byte0, uint8_t& byte1);  // done

  ///
  /// Check if HV is enabled in a single super pixel
  int IsHVEnabled(uint8_t superPixel, bool& enabled);  // done, not tested

  ///
  /// Returns vector with status of all super pixels index
  int WhichHVEnabled(
      std::vector<bool>& enabled);  // done, not tested, not SWIG wrapped

  ///
  /// Disables the HV on a specific super pixel
  int DisableHVSuperPixel(uint8_t superPixel);  // done

  ///
  /// Enables the HV on a specific super pixel
  int EnableHVSuperPixel(uint8_t superPixel);  // done

  ///
  /// Disables the HV to all super pixels on module
  int DisableHVAll();  // done

  ///
  /// Enables the HV to all super pixels on module
  int EnableHVAll();  // done

  ///
  /// Set the DAC value for the HV regulator on super pixel
  /// Voltage range roughly 10 V, val = 0 => high, val => 255 is low (it is a
  /// resistor)
  int SetHVDAC(uint8_t superPixel,
               uint8_t val);  // internally decide on device 4 x 4 devices, done

  ///
  /// Read back the DAC value that is used to regulate the HV on super pixel
  int ReadHVDAC(
      uint8_t superPixel,
      uint8_t& val);  // internally decide on device 4 x 4 devices, done

  ///
  /// Helper function, that set the HV DAC for all super pixels to the same
  /// value
  int SetHVDACAll(uint8_t dacVal);  // done, not tested

  ///
  /// Helper function to map super pixel id to address of the
  /// one of the four I2C-HV-regulator devices
  int SuperPixelIdToI2CAddr(uint8_t spId);  // done

  ///
  /// Helper function to map super pixel id to register
  /// address on the I2C device
  int SuperPixelIdToI2CRegAddr(uint8_t spId);  // done

  ///
  /// Helper function to map the super pixel id to
  /// the enable line on the I2C I/O extender
  int SuperPixelIdToHVEneableBit(uint8_t spId);  // done

  //////////////////////
  /// I2C fuctions end //
  //////////////////////

  ///
  /// Helper function to get measured HV
  /// for a super pixel
  int GetHVSuperPixel(uint8_t superPixel, float& val);

  /// there is a additional FPGA register to read HV superpixels with an ADC

  //////////////////////
  /// EEPROM FUNCTIONS
  /////////////////////

 private:
  ///
  /// Read Value (0-255) from address (0-127) on Primary EEPROM
  int ReadFromPrimaryEEPROM(uint8_t addrOnEEPROM, uint8_t& val);

  ///
  /// Write Value (0-255) to address (0-127) on Primary EEPROM
  int WriteToPrimaryEEPROM(uint8_t addrOnEEPROM, uint8_t value);

 public:
  int ModifyModuleIP(uint8_t value) { return WriteToPrimaryEEPROM(8, value); }
  int ReadModuleIP(uint8_t& val) { return ReadFromPrimaryEEPROM(8, val); }

  ///
  /// Write Module Identifier into EEPROM
  int ModifyModuleIdentifier(uint16_t value) {
    int stat;
    // splilt up val
    uint8_t val12 = (value & 0xFF);
    uint8_t val13 = ((value >> 8) & 0xFF);
    stat = WriteToPrimaryEEPROM(12, val12);
    if (stat != TC_OK) {
      return stat;
    }
    return WriteToPrimaryEEPROM(13, val13);
  }
  ///
  /// Read Module Identifier into EEPROM
  int ReadModuleIdentifier(uint16_t& val) {
    val = 0;
    uint8_t val13, val12;
    int stat = ReadFromPrimaryEEPROM(13, val13);
    if (stat != TC_OK) {
      return stat;
    }
    val = val13;
    val = val << 8;
    stat = ReadFromPrimaryEEPROM(12, val12);
    val |= val12;
    return stat;
  }

};  // TargetModule
}  // namespace TargetDriver
}  // namespace CTA
#endif  // INCLUDE_TARGETDRIVER_TARGETMODULE_H_
