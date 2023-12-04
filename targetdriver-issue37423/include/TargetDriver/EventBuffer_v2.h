#ifndef INCLUDE_TARGETDRIVER_EVENTBUFFER_H_
#define INCLUDE_TARGETDRIVER_EVENTBUFFER_H_

#include <iostream>
#include <memory>
#include <mutex>  // NOLINT(build/c++11), <mutex> is supported by GCC 4.4.7
#include <vector>

#include "TargetDriver/DataPacket_v2.h"
#include "TargetDriver/RawEvent_v2.h"
#include "TargetDriver/RingBuffer.h"

namespace CTA {
namespace TargetDriver {

class EventBuffer_v2 {
private:
  bool fFlushed;

  RingBuffer fEventBuffer;
  RingBuffer fDataPacketBuffer;
  std::vector<RawEvent_v2*> fEventVector;
  std::vector<DataPacket_v2*> fDataPacketVector;
  inline RawEvent_v2* GetEventAtIndex (int64_t i) const { return fEventVector[i]; }
  inline DataPacket_v2* GetDataPacketAtIndex (int64_t i) const { return fDataPacketVector[i]; }

  /// Statistics
  std::vector<uint32_t> fPacketsArrivedByPID;
  uint32_t fPacketsArrived,fPacketsDropped;
  uint32_t fEventsBuilt,fEventsRead,fEventsTimedOut,fEventsForcedOut,fEventsOverwritten;
  uint32_t fFailedWaveformChecks,fWaveformChecks;
  uint32_t fCheckFreq;  // how often to look in to packets (every nth packet)

  void InitializeMembers();
  inline uint64_t getTimeStamp(void) {
    timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (static_cast<uint64_t>(ts.tv_sec))*1000000000+(static_cast<uint64_t>(ts.tv_nsec));
  }

public:
  EventBuffer_v2(uint32_t pBufferDepth, uint16_t pNPacketsPerEvent, uint16_t pPacketSize, float pBuildTimeout = 0.2f, uint32_t pCheckFreq = 0);
  // MBG: Are we sure all the memory is freed?
  virtual ~EventBuffer_v2();
  void Clear();
  void ClearEvents();  // need to clear after flushing before reusing buffer
  inline uint16_t GetNPacketsPerEvent () const {
    if (fEventVector[0]) { return fEventVector[0]->GetNPacketsPerEvent(); }
    else return 0;
  }
  inline uint16_t GetPacketSize () const {
    if (fDataPacketVector[0]) { return fDataPacketVector[0]->GetPacketSize(); }
    else return 0;
  }

  // Returns the next available DataPacket where data can be written
  DataPacket_v2* GetAvailableDataPacket();
  // Confirms that the DataPacket has been filled with valid data
  bool PushAvailableDataPacket(DataPacket_v2 *pDataPacket);
  // Checks if a new DataPacket has been pushed and tries to associate it into an Event
  bool BuildSingleDataPacket();
  // Returns the next Event available to be written to disk/sent to Array Event Builder
  RawEvent_v2* ReadEvent();
  // Clears the events that have been "SetToRead" and marks all associated DataPackets as processed
  bool ClearProcessedEvents();
  // Clears all DataPackets that have been marked as processed
  bool ClearProcessedDataPackets();
  // allows all events in buffer to be read
  void Flush();

  inline bool IsFlushed() const { return fFlushed; }

  bool StatusOK() const;
  float GetEventRate();
  void Report(std::ostream& stream) const;
  void DiagnosticReport(std::ostream& stream) const;
};

}  // namespace TargetDriver
}  // namespace CTA

#endif  // INCLUDE_TARGETDRIVER_EVENTBUFFER_H_
