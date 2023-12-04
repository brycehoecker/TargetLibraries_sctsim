// Copyright (c) 2015 The CTA Consortium. All rights reserved.
/*! \file */
#ifndef INCLUDE_TARGETDRIVER_TESTERBOARD_H_
#define INCLUDE_TARGETDRIVER_TESTERBOARD_H_

#include <string>

#include "TargetDriver/TargetModule.h"

#define TESTER_BOARD_PORT 8104    // FIXED: testerboard port
#define TESTER_COMMAND_PORT 8103  // Arbitary: testerboard command port

namespace CTA {
namespace TargetDriver {

/*!
@class TesterBoard
@brief A class for TARGET 5 tester boards that are used to test CHEC-M
modules without a backplane. This is a ripped out of the libCHEC
*/
class TesterBoard : public TargetModule {
 public:
  virtual ~TesterBoard() {}
  ///
  ///
  int Init(const std::string& my_ip, const std::string& tb_ip);
  ///
  /// Register 0x10000, bit 31-0
  uint32_t GetFirmwareVersion() { return ReadReg(0x10000); }

  // Register 0x10001, bit 31-0
  // not implemented yet
  ////
  /// Register 0x10002-0x10003, bit 32-0
  uint64_t GetSerialNumber() {
    return (uint64_t(ReadReg(0x10003)) << 32) | ReadReg(0x10002);
  }

  // Register 0x10004, bit 31-12
  // Unused
  ///
  /// Register 0x10004, bit 11-0
  uint32_t GetStatus() { return ReadReg(0x10004); }
  void PrintStatus();

  // Register 0x10005, bit 31-0
  // not implemented yet

  // Register 0x10006, bit 31-20
  // Unused
  ///
  /// Register 0x10006, bit 19-0
  /// void SwitchAnalogInput(uint8_t asic, uint8_t channel);
  void TurnOffAnalogInput() { WriteRegister(0x10006, 0x0); }

  // Register 0x10007, bit 31-4, unused(?) documentation says it is used for
  // trigger dead time, but it exists in 0x1000E
  /// Register 0x10007, bit 3
  bool IsCameraModuleConnected() {
    return ReadReg(0x10007) & 0x8 ? false : true;
  }
  /// Register 0x10007, bit 2 and 0
  /// Set the levels of BP4 and BP6 lines. The result must be checked with
  /// T5CameraModule::GetStatusOfBP4 and T5CameraModule::GetStatusOfBP6.
  void SetStatusOfBPLines(bool bp6, bool bp4);
  /// Register 0x10007, bit 1
  void EnableReset(bool enable) {
    WriteRegisterPartially(0x10007, 1, 1, enable ? 0x0 : 0x1);
  }

  // Register 0x10008, bit 31-16 not implemented yet
  // Register 0x10008, bit 15-0  not implemented yet

  // Register 0x10009, bit 31-16 not implemented yet
  // Register 0x10009, bit 15-0  not implemented yet

  // Register 0x1000A, bit 31-16 Unused
  // Register 0x1000A, bit 15-0  not implemented yet

  // Register 0x1000B, bit 31-0 Unused

  // Register 0x1000C, bit 31    Always 1
  // Register 0x1000C, bit 30-28 Unused
  // Register 0x1000C, bit 27-23 Unused
  /// Register 0x1000C, bit 22-16, and register 0x1000D, bit 15-0
  // uint16_t ReadFPGAMonitor(uint8_t address);
  // double GetMeasuredHV(double offset);
  // Register 0x1000C, bit 15-0  not implemented yet

  // Register 0x1000D, bit 31    not implemented yet
  // Register 0x1000D, bit 30-28 Unused
  // Register 0x1000D, bit 27-23 Unused
  // Register 0x1000D, bit 22-16 not implemented yet

  /// Register 0x1000E, bit 31-16 Unused
  /// Register 0x1000E, bit 15-0
  /// @param deadtime deadtime x 8 (ns) will be the actual dead time
  int SetTriggerDeadTime(uint16_t deadtime) {
    return WriteRegisterPartially(0x1000E, 15, 0, deadtime);
  }

  // Register 0x1000F, bit 31    Unused
  // Register 0x1000F, bit 30-16 not implemented yet
  // Register 0x1000F, bit 15-8  Unused
  /// Register 0x1000F, bit 7-0
  /// Set the clock offset between a tester board and a camera module
  /// @param offset offset x 8 (ns)
  int SetClockOffset(uint8_t offset) {
    return WriteRegisterPartially(0x1000F, 7, 0, offset);
  }

  /// Register 0x10010, bit 31
  int SendSoftwareTrigger() {
    return WriteRegisterPartially(0x10010, 31, 31, 0x1);
  }
  /// Register 0x10010, bit 30
  void ResyncTrigger() {
    WriteRegisterPartially(0x10010, 31, 31, 0x0, 29, 29, 0x1);
    WriteRegisterPartially(0x10010, 31, 31, 0x0, 29, 29, 0x0);
  }
  // Register 0x10010, bit 29-22 Unused
  /// Register 0x10010, bit 21-18
  /// @param mode 0b00 - Regular trigger, 0b01, Sync related operation,
  /// 0b10/0b11 - Unused
  /// @param type When mode == 0b00, 0b00/0b01 - TACK with number of buffers and
  /// trigger delay for set 0/1
  /// 0b10 - software trigger, 0b11 - unused
  /// When mode == 0b01, 0b00 - intial sync command, 0b01, re-sync command,
  /// 0b10 - stop sync command, 0b11 - unused
  int SetTriggerModeAndType(uint8_t mode, uint8_t type);
  int SetTriggerMode(uint8_t mode) {
    return WriteRegisterPartially(0x10010, 21, 20, mode);
  }
  // Register 0x10010, bit 17
  // void EnableSoftwareTrigger(bool enable) {SetTriggerModeAndType(0b00,
  // 0b10);}
  /// Register 0x10010, bit 16

  void EnableExternalTrigger(bool enable) {
    SetTriggerModeAndType(0b00, 0b00);
    usleep(1000);
    WriteRegisterPartially(0x10010, 31, 31, 0);
    usleep(1000);
    WriteRegisterPartially(0x10010, 16, 16, enable ? 0x1 : 0x0);
    usleep(1000);
    /// HARM: code below is copied over from libCHEC, which might be wrong (and
    /// never tested)

    /*if (!enable) {
      // Re-sync mode ---> Stop trigger
      SetTriggerModeAndType(0b01, 0b10);
      usleep(1000);
      // Ensure software trigger bit is low
      WriteRegisterPartially(0x10010, 31, 31, 0);
      usleep(1000);
      // Disable software trigger
      WriteRegisterPartially(0x10010, 17, 17, 0);
      usleep(1000);
      // Disable external trigger
      WriteRegisterPartially(0x10010, 16, 16, enable ? 0x1 : 0);
      usleep(1000);
      // Sync mode ------> Allow triggering
      SetTriggerModeAndType(0b01, 0b00);
      usleep(1000);
    } else {
      // Re-sync mode ---> Stop trigger
      SetTriggerModeAndType(0b01, 0b10);
      // Ensure software trigger bit is low
      WriteRegisterPartially(0x10010, 31, 31, 0);
      usleep(1000);
      // Disable software trigger
      WriteRegisterPartially(0x10010, 17, 17, 0);
      usleep(1000);
      // Enable external trigger
      WriteRegisterPartially(0x10010, 16, 16, enable ? 0x1 : 0);
      usleep(1000);
      // Sync mode ------> Allow triggering
      SetTriggerModeAndType(0b01, 0b00);
      usleep(1000);
      // Change back to Ext trigger mode from Sync (this will send a TACK :( )
      SetTriggerModeAndType(0b00, 0b00);
      usleep(1000);
    }*/
  }
  void EnableSoftwareTrigger(bool enable) {
    if (!enable) {
      // Re-sync mode ---> Stop trigger
      SetTriggerModeAndType(0b01, 0b10);
      usleep(1000);
      // Ensure software trigger bit is low
      WriteRegisterPartially(0x10010, 31, 31, 0);
      usleep(1000);
      // Disable software trigger
      WriteRegisterPartially(0x10010, 17, 17, 0);
      usleep(1000);
      // Disable external trigger
      WriteRegisterPartially(0x10010, 16, 16, enable ? 0x1 : 0);
      usleep(1000);
    } else {
      // Enable software trigger
      WriteRegisterPartially(0x10010, 17, 17, enable ? 0x1 : 0);
      usleep(1000);
      // Sync mode ------> Allow triggering
      SetTriggerModeAndType(0b01, 0b00);
      usleep(1000);
      // Change back to SW trigger mode from Sync (this will send a TACK :( )
      SetTriggerModeAndType(0b00, 0b10);
      usleep(1000);
    }
  }

  uint8_t GetTriggerMode() { return (ReadReg(0x10010) >> 16) & 0x3; }
  /// Register 0x10010, bit 15-0
  void EnableTrigger(uint8_t asic, bool b0, bool b1, bool b2, bool b3);
  void EnableTrigger(uint8_t asic, uint8_t group, bool enable);

  // Register 0x10011, bit 31-16 Unused
  /// Register 0x10011, bit 15-0 (is this really only for internal triggers?)
  void EnableTriggerCounterContribution(uint8_t asic, uint8_t group,
                                        bool enable);

  // Register 0x10012, bit 31 not implemented yet
  /// Register 0x10012, bit 30-0
  /// @breif Start the trigger efficiency counter
  /// @param duration duration x 8 (ns) will be the actual length
  void StartTriggerEfficiencyCounter(uint32_t duration) {
    WriteRegisterPartially(0x10012, 30, 0, duration);
  }

  // Register 0x10013, bit 31   not implemented yet
  /// Register 0x10013, bit 30-0
  uint32_t GetTriggerCounter() { return ReadReg(0x10013) & 0x7FFFFFFF; }

  // Register 0x10014, bit 31   not implemented yet
  /// Register 0x10014, bit 30-0
  uint32_t GetTriggerEfficiencyCounter() {
    return ReadReg(0x10014) & 0x7FFFFFFF;
  }

  /// Register 0x10015, bit 31-3, Register 0x10016, bit 31-0
  /// Start time base counting in system clock cycles (8 ns)
  void StartTimeBaseCounting(uint64_t start);
  // Register 0x10015, bit 2-0  MBZ

  /// Register 0x10017-0x10018, bit 31-0
  uint64_t GetTACKMessage() {
    return (uint64_t(ReadReg(0x10018)) << 32) | ReadReg(0x10017);
  }

  /// Register 0x10019, bit 31 Not implemented yet
  bool IsTriggerEfficiencyCounterOutsideDeadTimeCompleted() {
    return ReadReg(0x10019) >> 31;
  }
  /// Register 0x10019, bit 30-0
  uint32_t GetTriggerEfficiencyCounterOutsideDeadTime() {
    return ReadReg(0x10019) & 0x7FFFFFFF;
  }

 private:
  uint32_t ReadReg(uint32_t address) {
    uint32_t val = 0;
    int stat = ReadRegister(address, val);
    if (stat != TC_OK)
      std::cout << "ReadReg() failed: " << ReturnCodeToString(stat)
                << std::endl;
    return val;
  }

  int WriteRegisterPartially(uint32_t address, uint8_t msb, uint8_t lsb,
                             uint32_t value);
  int WriteRegisterPartially(uint32_t address, uint8_t msb1, uint8_t lsb1,
                             uint32_t value1, uint8_t msb2, uint8_t lsb2,
                             uint32_t value2);
  int WriteRegisterPartially(uint32_t address, uint8_t msb1, uint8_t lsb1,
                             uint32_t value1, uint8_t msb2, uint8_t lsb2,
                             uint32_t value2, uint8_t msb3, uint8_t lsb3,
                             uint32_t value3);
};

}  // namespace TargetDriver
}  // namespace CTA

#endif  // INCLUDE_TARGETDRIVER_TESTERBOARD_H_
