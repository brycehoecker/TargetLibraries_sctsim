// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#ifndef INCLUDE_TARGETIO_EVENTFILEREADER_H_
#define INCLUDE_TARGETIO_EVENTFILEREADER_H_

#include <TargetDriver/EventHeader.h>

#include <string>

#include "TargetIO/EventFile.h"

namespace CTA {
namespace TargetIO {

class EventFileReader : public EventFile {
 protected:
  uint16_t fPacketSize;    //!< Event packet size in bytes
  uint8_t* fData;          //!< Byte array to be used to copy an event packet
  uint8_t fNEventHeaders;  //!< Number of event headers
  int32_t fEventHeaderVersion;  //!< Event header version
  uint32_t fNPacketsPerEvent;   //!< Number of event packets per event

  bool GetEventHeaderFast(uint32_t pEventIndex,
                          CTA::TargetDriver::EventHeader& pHeader);  // NOLINT

 public:
  explicit EventFileReader(const std::string& pFileName);
  virtual ~EventFileReader();

  void Close();
  bool GetEventHeader(uint32_t pEventIndex,
                      CTA::TargetDriver::EventHeader& pHeader);  // NOLINT
  uint8_t* GetEventPacket(uint32_t pEventIndex, uint16_t pPacketID);
  uint16_t GetPacketSize() const { return fPacketSize; }

  virtual uint32_t GetNEvents() const {
    if (!IsOpen()) return 0u;
    int64_t nrows = (const_cast<EventFileReader*>(this))->GetNrows();
    if (nrows > 0xffffffff) {
      std::cerr << "The number of events in this file looks to be too big ("
                << nrows << ").";
    }
    return static_cast<uint32_t>(nrows);
  }

  uint32_t GetNPacketsPerEvent() const { return fNPacketsPerEvent; }
  void ReadConfig(std::string& pConfig);  // NOLINT(runtime/references)
  int16_t GetSN(uint16_t slot);
  float GetSiPMTemp(uint16_t slot);
  float GetPrimaryTemp(uint16_t slot);
  int16_t GetSPDAC(uint16_t slot, uint16_t sp);
  int16_t GetSPHVON(uint16_t slot, uint16_t sp);
  std::string GetCameraVersion();
};

}  // namespace TargetIO
}  // namespace CTA

#endif  // INCLUDE_TARGETIO_EVENTFILEREADER_H_
