// Copyright (c) 2015 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains ModuleSimulation class
 *
*/

#ifndef INCLUDE_TARGETDRIVER_MODULESIMULATOR_H_
#define INCLUDE_TARGETDRIVER_MODULESIMULATOR_H_

#include <netinet/in.h>
#include <sys/socket.h>

#include <sys/time.h>
#include <thread>  // NOLINT(build/c++11)
#include <vector>

#include "TargetDriver/DataPacket.h"
#include "TargetDriver/TargetModule.h"
#include "TargetDriver/UDPServer.h"

namespace CTA {
namespace TargetDriver {
/*!
 * @class ModuleSimulator
 * @brief This is the class for simulating a target module via UDP packet
 *exchange
 *
 *
 */
class ModuleSimulator : public UDPServer {
  /*! \brief This is the class for simulating a target module via UDP packet
   *exchange
   * It will be well documented and written in simple C++.
   *
   * more detailed stuff should go here...
   */

 public:
  ModuleSimulator(const std::string& pModuleIP,
                  const std::string& pFPGADef = "",
                  const std::string& pASICDef = "",
                  const std::string& pTriggerASICDef = "",
                  double rate = 10 /*Hz*/);
  virtual ~ModuleSimulator() { Stop(); }
  ///

  /// Listen for slow control (read/write register) commands and respond to them
  void ListenAndRespond();

  /// Check if it is time to trigger, if so send event data
  void RunTrigger();

  /// Close the sockets used for data and slow control
  // TODO(Harm): Implement this if really needed. Definition is missing
  void CloseSockets() {}
  bool IsRunning() const { return fRunning; }
  void SetVerbose(bool verbose) { fVerbose = verbose; }
  void Start();
  void Stop();
  void StartTriggering();
  void StopTriggering();

  void SetTriggerRate(double pRate);
  bool CheckTimeDifference();
  void SendEventData();
  void SetRefWaveform();

 private:
  bool fVerbose;  ///<! print debugging info if true
                  //  std::map<uint32_t, uint32_t> fRegisters;
  bool fRunning;
  std::thread fThreadControl;
  std::thread fThreadTriggering;
  RegisterSettings fTargetSettings;  //< (Register) Settings for this TM
  uint32_t fTriggerTimeIntervalUs;
  uint8_t fWaveformsPerPacket;
  uint8_t fNumberOfBuffers;
  bool fTriggering;
  uint64_t fEventNumber;
  struct timeval fRefTime;
  struct timeval fStartRefTime;
  std::vector<uint16_t*> fRefWaveforms;
  DataPacket* fDataPacket;
  uint32_t fTriggerCounter;
};

}  // namespace TargetDriver
}  // namespace CTA

#endif  // INCLUDE_TARGETDRIVER_MODULESIMULATOR_H_
