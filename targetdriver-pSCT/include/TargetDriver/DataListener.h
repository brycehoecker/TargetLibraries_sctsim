// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#ifndef INCLUDE_TARGETDRIVER_DATALISTENER_H_
#define INCLUDE_TARGETDRIVER_DATALISTENER_H_
/*
#include <TargetDriver/DataPacket.h>
#include <TargetDriver/UDPClient.h>
#include "TargetDriver/EventBuffer.h"
#include "TargetDriver/TargetModule.h"
*/
#include <string>
#include <thread>  // NOLINT(build/c++11)

#include "TargetDriver/DataPacket.h"
#include "TargetDriver/UDPClient.h"
#include "TargetDriver/EventBuffer.h"
#include "TargetDriver/TargetModule.h"

namespace CTA {
namespace TargetDriver {

class DataListener : public TargetDriver::UDPClient {
 public:
  DataListener(uint32_t pBufferDepth, uint16_t pNPacketsPerEvent,
               uint16_t pPacketSize, float pBuildTimeout = 0.2f,
               uint32_t pCheckFreq = 0);
  virtual ~DataListener();

  int AddDAQListener(const std::string& pMyIP) {
    return AddDataListener(pMyIP, TM_DAQ_PORT, TM_SOCK_BUF_SIZE_DAQ);
  }

  void StopListening();
  void StartListening();

  bool IsRunning() const { return fRunning; }

  void DropPackets(bool drop = true) { fDropPackets = drop; }

  uint64_t GetNPacketsReceived() const { return fNPacketsReceived; }
  uint64_t GetNPacketProblems() const { return fNPacketProblems; }
  std::shared_ptr<EventBuffer> GetEventBuffer() const { return fEventBuffer; }

 private:
  uint64_t fNPacketsReceived;
  uint64_t fNPacketProblems;

  std::shared_ptr<EventBuffer> fEventBuffer;
  std::thread fThread;  //<! A thread in which the Listen function runs
  bool fRunning;
  bool fDropPackets;
  void Listen();
};

}  // namespace TargetDriver
}  // namespace CTA

#endif  // INCLUDE_TARGETDRIVER_DATALISTENER_H_
