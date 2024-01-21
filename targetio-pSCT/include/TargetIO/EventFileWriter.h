// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#ifndef INCLUDE_TARGETIO_EVENTFILEWRITER_H_
#define INCLUDE_TARGETIO_EVENTFILEWRITER_H_
/*
#include <TargetDriver/DataListener.h>
#include <TargetDriver/EventHeader.h>
#include <TargetDriver/EventBuffer.h>
#include <TargetDriver/RawEvent.h>
#include "TargetIO/EventFile.h"
#include "TargetIO/EventFileReader.h"
*/
#include <string>
#include <thread>  // NOLINT(build/c++11), <thread> is supported by GCC 4.4.7

#include <TargetDriver/DataListener.h>
#include <TargetDriver/EventHeader.h>
#include <TargetDriver/EventBuffer.h>
#include <TargetDriver/RawEvent.h>
#include "EventFile.h"
#include "EventFileReader.h"

namespace CTA {
namespace TargetIO {

class EventFileWriter : public EventFile {
 public:
  EventFileWriter(const std::string& pFileName, uint16_t pNPacketsPerEvent,
                  uint16_t pPacketSizeInByte);

  // For creating calibrated R1 file
  EventFileWriter(const std::string& pR1FileName,
                  CTA::TargetIO::EventFileReader* pR0Reader);
  virtual ~EventFileWriter() { Close(); }

  void AddComment(const std::string& pComment);
  void AddHistory(const std::string& pHistory);
  void AddCardImage(const std::string& pKeyword, bool pValue,
                    const std::string& pComment, bool pUpdate = false);
  void AddCardImage(const std::string& pKeyword, double pValue,
                    const std::string& pComment, bool pUpdate = false);
  void AddCardImage(const std::string& pKeyword, float pValue,
                    const std::string& pComment, bool pUpdate = false);
  void AddCardImage(const std::string& pKeyword, uint8_t pValue,
                    const std::string& pComment, bool pUpdate = false) {
    AddCardImage(pKeyword, int32_t(pValue), pComment, pUpdate);
  }
  void AddCardImage(const std::string& pKeyword, uint16_t pValue,
                    const std::string& pComment, bool pUpdate = false) {
    AddCardImage(pKeyword, int32_t(pValue), pComment, pUpdate);
  }
  void AddCardImage(const std::string& pKeyword, uint32_t pValue,
                    const std::string& pComment, bool pUpdate = false) {
    AddCardImage(pKeyword, int64_t(pValue), pComment, pUpdate);
  }
  void AddCardImage(const std::string& pKeyword, int32_t pValue,
                    const std::string& pComment, bool pUpdate = false);
  void AddCardImage(const std::string& pKeyword, int64_t pValue,
                    const std::string& pComment, bool pUpdate = false);
  void AddCardImage(const std::string& pKeyword, const std::string& pValue,
                    const std::string& pComment, bool pUpdate = false);
  void AddCardImage(const std::string& pKeyword, const char* pValue,
                    const std::string& pComment, bool pUpdate = false) {
    AddCardImage(pKeyword, std::string(pValue), pComment, pUpdate);
  }

  void AddEvent(TargetDriver::RawEvent* pRawEvent);
  void Close(bool pWriteDateEnd = true);
  void Flush();

  void StartWatchingBuffer(
      std::shared_ptr<TargetDriver::EventBuffer> pEventBuffer);
  void StopWatchingBuffer();
  void SetWatcherSleep(useconds_t pSleepUs) { fWatcherSleep = pSleepUs; }

  void WriteConfig(const std::string& pConfig);

  static std::shared_ptr<EventFileWriter> MakeEventFileWriter(
      const CTA::TargetDriver::DataListener& listener,
      const std::string& fname);

  void DoNotWrite() {fWriting=false;}

  int GetPacketsWritten() {return fPacketsWritten;}

 private:
  std::thread fThread;  //<! A thread in which the Watcher function runs
  std::shared_ptr<TargetDriver::EventBuffer> fEventBuffer;
  bool fWatching;
  bool fWriting;
  uint32_t fEventsWritten;
  uint32_t fPacketsWritten;
  
  useconds_t fWatcherSleep;  //<! sleep between attempted reads and flushes

  void InitBinaryTable(uint16_t pNPacketsPerEvent, uint16_t pPacketSizeInByte);
  void InitConfigImage(uint32_t pSizeInByte);

  void Watcher();  //<! function run in the thread
};

}  // namespace TargetIO
}  // namespace CTA

#endif  // INCLUDE_TARGETIO_EVENTFILEWRITER_H_
