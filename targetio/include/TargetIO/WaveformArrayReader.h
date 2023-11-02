// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#ifndef INCLUDE_TARGETIO_WAVEFORMARRAYREADER_H_
#define INCLUDE_TARGETIO_WAVEFORMARRAYREADER_H_

#include <cstdio>
#include <climits>
#include <unistd.h>
#include <vector>
#include <memory>
#include <set>
#include <TargetDriver/DataPacket.h>
#include <TargetDriver/EventHeader.h>
#include "TargetIO/EventFileReader.h"

namespace CTA {
namespace TargetIO {

class WaveformArrayReader {
private:
  uint16_t fNASICs;
  uint16_t fNChannels;
  uint16_t fSkipEvents;
  uint16_t fSkipEndEvents;
  uint8_t fFirstModule;

  uint16_t fPacketSize;
  uint32_t fNPacketsPerEvent;
  CTA::TargetIO::EventFileReader* fReader;
  CTA::TargetDriver::DataPacket* fPacket;
  CTA::TargetDriver::Waveform fWf;
  CTA::TargetDriver::EventHeader fHeader;
  std::mutex fPacketMutex;

public:

  size_t fNEvents;
  size_t fFirstEventID;
  size_t fLastEventID;
  size_t fNPixels;
  size_t fNSuperpixelsPerModule;
  size_t fNModules;
  size_t fNSamples;
  uint32_t fRunID;
  std::string fCameraVersion;

  bool fR1;
  float fOffset;
  float fScale;

  explicit WaveformArrayReader(const std::string &filepath,
                               uint16_t skip_events=0,
                               uint16_t skip_end_events=0,
                               bool silent=false);

  ~WaveformArrayReader();

  uint32_t GetEventID(uint32_t event_index) {
    uint32_t event_id = event_index + fSkipEvents;
    if (event_id >= fNEvents + fSkipEvents) {
      std::cerr << "WARNING: Requested event id is out of range: "
                << event_id << std::endl;
    }
    return event_id;
  }

  uint32_t GetEventIndex(uint32_t event_id) {
    return event_id - fSkipEvents;
  }

  int16_t GetSN(uint16_t tm) {
    if (tm >= fNModules) {
      std::cout << "ERROR Requested TM out of range: " << tm << std::endl;
    }
    return fReader->GetSN(tm);
  }

  float GetSiPMTemp(uint16_t tm) {
    if (tm >= fNModules) {
      std::cout << "ERROR Requested TM out of range: " << tm << std::endl;
    }
    return fReader->GetSiPMTemp(tm);
  }

  float GetPrimaryTemp(uint16_t tm) {
    if (tm >= fNModules) {
      std::cout << "ERROR Requested TM out of range: " << tm << std::endl;
    }
    return fReader->GetPrimaryTemp(tm);
  }

  int16_t GetSPDAC(uint16_t tm, uint16_t sp) {
    if (tm >= fNModules) {
      std::cout << "ERROR Requested TM out of range: " << tm << std::endl;
    }
    if (sp >= fNSuperpixelsPerModule) {
      std::cout << "ERROR Requested SP out of range: " << sp << std::endl;
    }
    return fReader->GetSPDAC(tm, sp);
  }

  int16_t GetSPHVON(uint16_t tm, uint16_t sp) {
    if (tm >= fNModules) {
      std::cout << "ERROR Requested TM out of range: " << tm << std::endl;
    }
    if (sp >= fNSuperpixelsPerModule) {
      std::cout << "ERROR Requested SP out of range: " << sp << std::endl;
    }
    return fReader->GetSPHVON(tm, sp);
  }

  void GetR0Event(uint32_t event_index,
                  uint16_t* waveforms, size_t n_pixels_w, size_t n_samples_w,
                  uint16_t& first_cell_id, bool& stale, bool& missing_packets,
                  uint64_t& tack, int64_t& cpu_s, int64_t& cpu_ns);

  void GetR1Event(uint32_t event_index,
                  float* waveforms, size_t n_pixels_w, size_t n_samples_w,
                  uint16_t& first_cell_id, bool& stale, bool& missing_packets,
                  uint64_t& tack, int64_t& cpu_s, int64_t& cpu_ns);

};

}  // namespace TargetIO
}  // namespace CTA

#endif //INCLUDE_TARGETIO_WAVEFORMARRAYREADER_H_
