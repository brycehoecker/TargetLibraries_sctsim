// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#ifndef INCLUDE_TARGETDRIVER_RAWEVENT_H_
#define INCLUDE_TARGETDRIVER_RAWEVENT_H_

#include <TargetDriver/DataPacket.h>
#include <sys/time.h>

#include <memory>
#include <vector>

#include "TargetDriver/EventHeader.h"

namespace CTA {
namespace TargetDriver {

class RawEvent {
 public:
  RawEvent(uint16_t pNPacketsPerEvent, uint16_t pPacketSize);
  virtual ~RawEvent() {}

  void Clear();
  //  const std::vector<std::shared_ptr<CTA::TargetDriver::DataPacket> >&
  const std::vector<DataPacket*>& GetDataPackets() const {
    return fDataPackets;
  }
  uint16_t GetPacketSize() const {
    return fDataPackets.size() > 0 ? fDataPackets[0]->GetPacketSize() : 0;
  }
  EventHeader& GetEventHeader() { return fEventHeader; }
  std::size_t GetNPacketsPerEvent() const { return fDataPackets.size(); }
  double GetTimeoutSec() const { return fTimeoutSec; }
  static void SetTimeoutSec(double pTimeoutSec) { fTimeoutSec = pTimeoutSec; }
  bool IsEmpty() const { return fEventHeader.GetNPacketsFilled() == 0; }
  bool IsTimedOut();
  bool WasFlushed() const { return fFlushed; }
  bool WasRead() const { return fRead; }
  void SetToRead() { fRead = true; }
  void SetToFlushed() { fFlushed = true; }

  bool IsBeingBuilt() const;
  bool IsComplete() const {
    return fEventHeader.GetNPacketsFilled() == fDataPackets.size();
  }
  bool AddNewPacket(const uint8_t* pData, uint16_t pPacketID,
                    uint16_t pPacketSize, bool checkflag = false);
  bool WaveformCheckStatus() { return fWaveformCheckStatus; }

 private:
  EventHeader fEventHeader;
  //  std::vector<std::shared_ptr<CTA::TargetDriver::DataPacket> > fDataPackets;
  std::vector<DataPacket*> fDataPackets;

  static double fTimeoutSec;  // in seconds

  /// true if >= 1 packet has arrived - but event is not yet complete
  bool fTimedOut;
  bool fFlushed;
  bool fRead;

  bool fWaveformCheckStatus;
};

inline bool RawEvent::IsBeingBuilt() const {
  if (fEventHeader.GetNPacketsFilled() == 0 ||
      fEventHeader.GetNPacketsFilled() == fDataPackets.size()) {
    return false;
  }

  return true;
}

/// Returns true if this event is timed out (i.e., not all of expected data
/// packets did not arrive within fTimedOut).
inline bool RawEvent::IsTimedOut() {
  if (fTimedOut) {
    return true;
  }

  if (fEventHeader.IfTimeStampIsZero()) {  // first packet not arrived yet
    return false;
  }

  double dt = fEventHeader.CalcDeltaTSinceTimeStamp();
  if (dt > fTimeoutSec) {
    fTimedOut = true;
  }

  return fTimedOut;
}

}  // namespace TargetDriver
}  // namespace CTA

#endif  // INCLUDE_TARGETDRIVER_RAWEVENT_H_
