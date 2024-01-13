// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#ifndef INCLUDE_TARGETDRIVER_RAWEVENT_H_
#define INCLUDE_TARGETDRIVER_RAWEVENT_H_

#include <TargetDriver/DataPacket_v2.h>
#include <sys/time.h>

#include <memory>
#include <vector>

#include "TargetDriver/EventHeader.h"

namespace CTA {
namespace TargetDriver {

class RawEvent_v2 {
  private:
   EventHeader fEventHeader;
   std::vector<DataPacket_v2*> fDataPackets;
   double fTimeoutSec;  // in seconds
   bool fTimedOut;
   bool fFlushed;
   bool fRead;
   bool fWaveformCheckStatus;

 public:
  RawEvent_v2(uint16_t pNPacketsPerEvent, uint16_t pPacketSize, bool pCreatePackets=true);
  // NOTE(MBG): Should delete the events if they were created... Memory leak potential
  virtual ~RawEvent_v2() {}
  void Clear();

  //  const std::vector<std::shared_ptr<CTA::TargetDriver::DataPacket> >&
  inline EventHeader& GetEventHeader() { return fEventHeader; }
  inline const std::vector<DataPacket_v2*>& GetDataPackets() const { return fDataPackets; }

  inline uint16_t GetPacketSize() const {
    return ((fDataPackets.size() > 0)&&(fDataPackets[0]!=NULL)) ? fDataPackets[0]->GetPacketSize() : 0;
  }

  inline std::size_t GetNPacketsPerEvent() const { return fDataPackets.size(); }
  inline bool WaveformCheckStatus() { return fWaveformCheckStatus; }

  /// MBG: Can be optimized so we don't have to call the "time" function all time. Use "expiration date" instead!
  /// Returns true if this event is timed out (i.e., not all of expected data
  /// packets did not arrive within fTimedOut).
  inline void SetTimeoutSec(double pTimeoutSec) { fTimeoutSec = pTimeoutSec; }
  inline double GetTimeoutSec() const { return fTimeoutSec; }
  inline bool IsTimedOut() {
    if (fTimedOut) { return true; }
    if (fEventHeader.IfTimeStampIsZero()) { return false; }
    double dt = fEventHeader.CalcDeltaTSinceTimeStamp();
    if (dt > fTimeoutSec) { fTimedOut = true; }
    return fTimedOut;
  }

  inline void SetToFlushed() { fFlushed = true; }
  inline bool WasFlushed() const { return fFlushed; }
  inline void SetToRead() { fRead = true; }
  inline bool WasRead() const { return fRead; }

  inline bool IsEmpty() const { return fEventHeader.GetNPacketsFilled() == 0; }
  inline bool IsComplete() const { return fEventHeader.GetNPacketsFilled() == fDataPackets.size(); }
  inline bool IsBeingBuilt() const { return (!(IsEmpty()||IsComplete())); }

  //bool AddNewPacket(const uint8_t* pData, uint16_t pPacketID,uint16_t pPacketSize, bool checkflag = false);

  bool AssociatePacket (DataPacket_v2* pDataPacket, uint16_t packetID, bool checkflag=false);
  bool DissociatePacket (uint16_t packetID);
  bool DissociateAllPackets ();

};

}  // namespace TargetDriver
}  // namespace CTA

#endif  // INCLUDE_TARGETDRIVER_RAWEVENT_H_
