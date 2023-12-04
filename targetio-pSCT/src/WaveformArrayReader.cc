// Copyright (c) 2015 The CTA Consortium. All rights reserved.

#include "TargetIO/WaveformArrayReader.h"

namespace CTA {
namespace TargetIO {

WaveformArrayReader::WaveformArrayReader(const std::string &filepath,
                    uint16_t skip_events, uint16_t skip_end_events, bool silent)
{ 
  // Test for "SCT support on compilation, CHEC-S by default" behavior
  #ifdef SCT
    std::cout << "test successful" << std::endl;
  #else
    std::cout << "test failed" << std::endl;
  #endif

  fReader = new CTA::TargetIO::EventFileReader(filepath);
  fPacketSize = fReader->GetPacketSize();
  fNPacketsPerEvent = fReader->GetNPacketsPerEvent();
  fPacket = new CTA::TargetDriver::DataPacket(fPacketSize);

  // Test for "SCT support on compilation, CHEC-S by default" behavior
  #ifdef SCT
    std::cout << "test successful" << std::endl;
  #else
    std::cout << "test failed" << std::endl;
  #endif

  // Get number of modules and first module id
  std::set<uint8_t> module_set;
  for (uint16_t ipack =0; ipack < fNPacketsPerEvent; ipack++) {
    uint8_t* eventPacket = fReader->GetEventPacket(0, ipack);
    fPacket->Assign(eventPacket, fPacketSize);
#ifdef SCT
    uint8_t module = fPacket->GetDetectorID();
#else
    uint8_t module = fPacket->GetSlotID();
#endif
    module_set.insert(module);
  }
  size_t nModulesInFile = module_set.size();
  uint8_t firstModule = *module_set.begin();

  // Hardcoded n_module situations
  if (nModulesInFile == 1) {
    fNModules = 1; // Single module case
  }
  if (nModulesInFile > 1 && nModulesInFile <= 24) {
      fNModules = 24;
      firstModule = 0;
  }
  else if (nModulesInFile > 1 && nModulesInFile <= 32) {
    fNModules = 32; // CHEC Camera case
    firstModule = 0;
  }
  else {
    fNModules = nModulesInFile;
    std::cerr << "WARNING: No case set up for files with N modules:"
              << nModulesInFile << std::endl;
  }

  // Read Run ID
  fRunID = 0;
  if (fReader->HasCardImage("RUNNUMBER")) {
    fRunID = uint32_t(fReader->GetCardImage("RUNNUMBER")->GetValue()->AsInt());
  }

  // Read R1
  std::string comment;
  fR1 = false;
  fOffset = 0;
  fScale = 0;
  if (fReader->HasCardImage("R1")) {
    fR1 = fReader->GetCardImage("R1")->GetValue()->AsBool();
    if (fR1) {
      fOffset = (float) fReader->GetCardImage("OFFSET")->GetValue()->AsDouble();
      fScale = (float) fReader->GetCardImage("SCALE")->GetValue()->AsDouble();
    }
  }

  fCameraVersion = fReader->GetCameraVersion();
  fFirstModule = firstModule;
  fNASICs = 4;
  fNChannels = 16;
  fNPixels = fNModules * fNASICs * fNChannels;
  fNSuperpixelsPerModule = 16;
  fSkipEvents = skip_events;
  fSkipEndEvents = skip_end_events;
  fNEvents = fReader->GetNEvents() - fSkipEvents - fSkipEndEvents;
  fFirstEventID = fSkipEvents;
  fLastEventID = fNEvents + fSkipEvents;

  uint8_t* eventPacket = fReader->GetEventPacket(0, 0);
  fPacket->Assign(eventPacket, fPacketSize);
  fPacket->AssociateWaveform(0, fWf);
  fNSamples = fWf.GetSamples();

  if (!silent) {
    std::cout << "[WaveformArrayReader] Path: " << filepath << std::endl;
    std::cout << "[WaveformArrayReader] CameraVersion: " << fCameraVersion << std::endl;
    std::cout << "[WaveformArrayReader] IsR1: " << fR1 << std::endl;
    std::cout << "[WaveformArrayReader] NModules: " << fNModules << std::endl;
    std::cout << "[WaveformArrayReader] ActiveModuleSlots: ";
    for (uint8_t slot: module_set) {
      std::cout << (unsigned) slot << " ";
    }
    std::cout << std::endl;
    std::cout << "[WaveformArrayReader] NPixels: " << fNPixels << std::endl;
    std::cout << "[WaveformArrayReader] SkipEvents: " << fSkipEvents << std::endl;
    std::cout << "[WaveformArrayReader] SkipEndEvents: " << fSkipEndEvents << std::endl;
    std::cout << "[WaveformArrayReader] NEvents: " << fNEvents << std::endl;
    std::cout << "[WaveformArrayReader] NSamples: " << fNSamples << std::endl;
  }

}


WaveformArrayReader::~WaveformArrayReader() {
  delete fReader;
  fReader = nullptr;
  delete fPacket;
  fPacket = nullptr;
}


void WaveformArrayReader::GetR0Event(
  uint32_t event_index,
  uint16_t* waveforms, size_t n_pixels_w, size_t n_samples_w,
  uint16_t& first_cell_id, bool& stale, bool& missing_packets,
  uint64_t& tack, int64_t& cpu_s, int64_t& cpu_ns
  ) {

  // Reset values to zero
  std::fill(waveforms, waveforms + n_pixels_w * n_samples_w, 0);
  first_cell_id = 0;
  stale = false;
  missing_packets = false;
  tack = 0;
  cpu_s = 0;
  cpu_ns = 0;

  // Check sizes
  if (n_pixels_w != fNPixels) {
    std::cerr << "WARNING: incorrect number of pixels "
      "in waveform array" << std::endl;
  }
  if (n_samples_w != fNSamples) {
    std::cerr << "WARNING: incorrect number of samples "
      "in waveform array" << std::endl;
  }

  uint32_t event_id = GetEventID(event_index);

  std::lock_guard<std::mutex> lockGuard(fPacketMutex);

  fReader->GetEventHeader(event_id, fHeader);
  fHeader.GetTimeStamp(cpu_s, cpu_ns);

  for (uint16_t ipack = 0; ipack < fNPacketsPerEvent; ipack++) {
    uint8_t* eventPacket = fReader->GetEventPacket(event_id, ipack);
    fPacket->Assign(eventPacket, fPacketSize);
    uint16_t nWaveforms = fPacket->GetNumberOfWaveforms();
    if (nWaveforms > 0) {
      first_cell_id = fPacket->GetFirstCellId();
      tack = fPacket->GetTACKTime();
      if (ipack == 0) fTACK_time = tack;
      if (fPacket->GetStaleBit() == 1) stale = true;
    } else missing_packets = true;
#ifdef SCT
    uint8_t module = fPacket->GetDetectorID() - fFirstModule;
#else
    uint8_t module = fPacket->GetSlotID() - fFirstModule;
#endif
    for (unsigned short iwav = 0; iwav < nWaveforms; iwav++) {
      fPacket->AssociateWaveform(iwav, fWf);
      uint16_t n_samples = fWf.GetSamples();
      uint8_t asic = fWf.GetASIC();
      uint8_t channel = fWf.GetChannel();
      uint16_t pix = module*fNASICs*fNChannels + asic*fNChannels + channel;
      for (unsigned short isam = 0; isam < n_samples; isam++) {
        waveforms[pix * fNSamples + isam] = fWf.GetADC(isam);
      }
    }
  }
}


void WaveformArrayReader::GetR1Event(
  uint32_t event_index,
  float* waveforms, size_t n_pixels_w, size_t n_samples_w,
  uint16_t& first_cell_id, bool& stale, bool& missing_packets,
  uint64_t& tack, int64_t& cpu_s, int64_t& cpu_ns
  ) {

  // Reset arrays to zero
  std::fill(waveforms, waveforms + n_pixels_w * n_samples_w, 0);
  first_cell_id = 0;
  stale = false;
  missing_packets = false;
  tack = 0;
  cpu_s = 0;
  cpu_ns = 0;

  // Check sizes
  if (n_pixels_w != fNPixels) {
    std::cerr << "WARNING: incorrect number of pixels "
      "in waveform array" << std::endl;
  }
  if (n_samples_w != fNSamples) {
    std::cerr << "WARNING: incorrect number of samples "
      "in waveform array" << std::endl;
  }

  uint32_t event_id = GetEventID(event_index);

  std::lock_guard<std::mutex> lockGuard(fPacketMutex);

  fReader->GetEventHeader(event_id, fHeader);
  fHeader.GetTimeStamp(cpu_s, cpu_ns);

  for (uint16_t ipack = 0; ipack < fNPacketsPerEvent; ipack++) {
    uint8_t* eventPacket = fReader->GetEventPacket(event_id, ipack);
    fPacket->Assign(eventPacket, fPacketSize);
    uint16_t nWaveforms = fPacket->GetNumberOfWaveforms();
    if (nWaveforms > 0) {
      first_cell_id = fPacket->GetFirstCellId();
      tack = fPacket->GetTACKTime();
      if (ipack == 0) {
          fTACK_time = tack;
    }
      if (fPacket->GetStaleBit() == 1) stale = true;
    } else missing_packets = true;
#ifdef SCT
    uint8_t module = fPacket->GetDetectorID() - fFirstModule;
#else
    uint8_t module = fPacket->GetSlotID() - fFirstModule;
#endif
    for (unsigned short iwav = 0; iwav < nWaveforms; iwav++) {
      fPacket->AssociateWaveform(iwav, fWf);
      uint16_t n_samples = fWf.GetSamples();
      uint8_t asic = fWf.GetASIC();
      uint8_t channel = fWf.GetChannel();
      uint16_t pix = module*fNASICs*fNChannels + asic*fNChannels + channel;
      for (unsigned short isam = 0; isam < n_samples; isam++) {
        waveforms[pix*fNSamples+isam] =
          ((float) fWf.GetADC16bit(isam)/fScale)-fOffset;
      }
    }
  }
}

void WaveformArrayReader::GetBlock(
  uint32_t event_index 
  ) {
  uint32_t event_id = GetEventID(event_index);
  uint8_t* blockPacket = fReader->GetEventPacket(event_id, 0);
  fPacket->Assign(blockPacket, fPacketSize);
  fBlock = fPacket->GetColumn() * 8 + fPacket->GetRow();
  fPhase = fPacket->GetBlockPhase();

} //Idea here is to be able give an event and pixel and get the correct block and block phase out of it

}  // namespace TargetIO
}  // namespace CTA
