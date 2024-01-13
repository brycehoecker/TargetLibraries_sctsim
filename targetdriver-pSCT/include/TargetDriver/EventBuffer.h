#ifndef INCLUDE_TARGETDRIVER_EVENTBUFFER_H_
#define INCLUDE_TARGETDRIVER_EVENTBUFFER_H_

//#define NEWEVBUILDING 

#include <iostream>
#include <memory>
#include <vector>

#include "TargetDriver/RawEvent.h"

namespace CTA {
namespace TargetDriver {

class EventBuffer {
 public:
  EventBuffer(uint32_t pBufferDepth, uint16_t pNPacketsPerEvent,
              uint16_t pPacketSize, float pBuildTimeout = 0.2f,
              uint32_t pCheckFreq = 0);
  virtual ~EventBuffer() {}

  bool AddNewPacket(const uint8_t* pData, uint32_t pEventID, uint16_t pPacketID,
                    uint16_t pPacketSize);
  /// called by file writing thread whenever possible
  //  std::shared_ptr<RawEvent> ReadEvent();
  RawEvent* ReadEvent();

  void Clear();
  void ClearEvents();  // need to clear after flushing before reusing buffer
  void Flush();        // allows all events in buffer to be read

  void Report(std::ostream& stream) const;
  bool StatusOK() const;

  float GetEventRate() const;

  uint16_t GetPacketSize() const {
    // TODO(Akira): memory check is needed?
    return fEventVector[0]->GetDataPackets()[0]->GetPacketSize();
  }
  uint16_t GetNPacketsPerEvent() const {
    // TODO(Akira): memory check is needed?
    return static_cast<uint16_t>(fEventVector[0]->GetDataPackets().size());
  }

  int64_t GetReadIndex() const {
    return std::distance(fBufferBegin, fReadIterator);
  }
  int64_t GetWriteIndex() const {
    return std::distance(fBufferBegin, fWriteIterator);
  }
  int64_t GetFinishedIndex() const {
    return std::distance(fBufferBegin, fFinishedIterator);
  }

  int64_t GetNumberIncomplete() const;
  int64_t GetNumberToBeRead() const;

  void DiagnosticReport(std::ostream& stream) const; 

 private:
  // typedef std::vector<std::shared_ptr<RawEvent> >::iterator buffer_it;
  typedef std::vector<RawEvent*>::iterator buffer_it;
  void AdvanceFinishedIterator(buffer_it pNextIterator);
  void InitializeMembers();

  //  std::vector<std::shared_ptr<RawEvent> > fEventVector;
  std::vector<RawEvent*> fEventVector;

  std::mutex fFinishedMutex;
  std::mutex fWriteMutex;

  /// Iterator of next event to be read from the buffer and written to a file
  buffer_it fReadIterator;
  /// Iterator of the last event which is finished (is complete or timed out)
  buffer_it fFinishedIterator;
  /// Iterator of the next available slot to start a new event
  buffer_it fWriteIterator;
  /// Points to fEventVector.end() to indicate that fFinishedIterator is not
  /// initialized and there is no complete events
  buffer_it fNoFinishedEvents;
  /// Points to fEventVector.end() to indicate that fWriteIterator is not
  /// initialized
  buffer_it fWriteIteratorNotInitialized;
  /// Points to fEventVector.begin()
  buffer_it fBufferBegin;
  /// Points to fEventVector.end()
  buffer_it fBufferEnd;
  buffer_it fBufferLast;

  /// Statistics
  std::vector<uint32_t> fPacketsArrivedByPID;
  uint32_t fPacketsArrived;
  uint32_t fPacketsDropped;
  uint32_t fEventsBuilt;
  uint32_t fEventsRead;
  uint32_t fEventsTimedOut;
  uint32_t fEventsOverwritten;
  uint32_t fFailedWaveformChecks;
  uint32_t fWaveformChecks;
  uint32_t fCheckFreq;  // how often to look in to packets (every nth packet)

  bool fFlushed;
};

}  // namespace TargetDriver
}  // namespace CTA

#endif  // INCLUDE_TARGETDRIVER_EVENTBUFFER_H_
