//
// Created by Jason Watson on 08/05/2017.
//

#ifndef TARGETCALIB_PEDESTALGENERATOR_H
#define TARGETCALIB_PEDESTALGENERATOR_H

#include <iostream>
#include <fstream>
#include <vector>
#include <unistd.h>
#include <set>

//TargetIO
#include "TargetIO/EventFileReader.h"

//TargetDriver
#include "TargetDriver/Waveform.h"
#include "TargetDriver/DataPacket.h"

//TargetCalib
#include "TargetCalib/PedestalMaker.h"

namespace CTA {
namespace TargetCalib {

class PedestalGenerator {
private:
  uint16_t fSkipSamples;
  uint16_t fSkipEndSamples;
  uint16_t fSkipEvents;
  uint16_t fSkipEndEvents;

  uint16_t fPacketSize;
  uint32_t fNPacketsPerEvent;
  CTA::TargetDriver::DataPacket *fPacket;
  CTA::TargetDriver::Waveform fWf;
  CTA::TargetDriver::EventHeader fHeader;

  CTA::TargetIO::EventFileReader *fReader;
  CTA::TargetCalib::PedestalMaker *fPedMaker;

  size_t fNEvents;
  uint16_t fNModules;
  uint8_t fFirstModule;
  uint16_t fNCells;
  uint16_t fNBlockSamples;
  uint16_t fNBlocks;
public:
  PedestalGenerator(std::string eventPath, uint16_t nCells,
                    uint16_t skipSamples = 0, uint16_t skipEndSamples = 0,
                    uint16_t skipEvents = 0, uint16_t skipEndEvents = 0,
                    bool diagnostic = false) {

    std::cout << "[PedestalGenerator] Opening Event File: "
              << eventPath << std::endl;
    fReader = new CTA::TargetIO::EventFileReader(eventPath);
    fPacketSize = fReader->GetPacketSize();
    fNPacketsPerEvent = fReader->GetNPacketsPerEvent();
    fPacket = new CTA::TargetDriver::DataPacket(fPacketSize);

    // Get number of modules and first module id
    std::set<uint8_t> module_set;
    for (uint16_t ipack = 0; ipack < fNPacketsPerEvent; ipack++) {
      uint8_t *eventPacket = fReader->GetEventPacket(0, ipack);
      fPacket->Assign(eventPacket, fPacketSize);
      uint8_t module = fPacket->GetSlotID();
      module_set.insert(module);
    }
    size_t nModulesInFile = module_set.size();
    fFirstModule = *module_set.begin();

    // Hardcoded n_module situations
    if (nModulesInFile == 1) {
      fNModules = 1; // Single module case
    }
    else if (nModulesInFile > 1 && nModulesInFile <= 32) {
      fNModules = 32; // CHEC Camera case
      fFirstModule = 0;
    }
    else {
      fNModules = (uint16_t) nModulesInFile;
      std::cerr << "WARNING: No case set up for files with N modules:"
                << nModulesInFile << std::endl;
    }

    fNCells = nCells;
    fNBlockSamples = N_BLOCKPHASE;
    fNBlocks = fNCells / fNBlockSamples;
    fSkipSamples = skipSamples;
    fSkipEndSamples = skipEndSamples;
    fSkipEvents = skipEvents;
    fSkipEndEvents = skipEndEvents;
    fNEvents = fReader->GetNEvents() - fSkipEvents - fSkipEndEvents;

    // Get event/waveform information
    uint8_t *eventPacket = fReader->GetEventPacket(0, 0);
    fPacket->Assign(eventPacket, fPacketSize);
    fPacket->AssociateWaveform(0, fWf);
    uint16_t nSamples = fWf.GetSamples() - fSkipSamples - fSkipEndSamples;

    std::cout << "[PedestalGenerator] EVENT FILE CONTENTS: " << std::endl;
    std::cout << "\t NModules: " << fNModules << std::endl;
    std::cout << "\t ActiveModuleSlots: ";
    for (uint8_t slot: module_set) {
      std::cout << (unsigned) slot << " ";
    }
    std::cout << std::endl;
    std::cout << "\t NCells: " << fNCells << std::endl;
    std::cout << "\t NBlockSamples: " << fNBlockSamples << std::endl;
    std::cout << "\t NBlocks: " << fNBlocks << std::endl;
    std::cout << "\t SkipSamples: " << fSkipSamples << std::endl;
    std::cout << "\t SkipEndSamples: " << fSkipEndSamples << std::endl;
    std::cout << "\t SkipEvents: " << fSkipEvents << std::endl;
    std::cout << "\t SkipEndEvents: " << fSkipEndEvents << std::endl;
    std::cout << "\t NEvents: " << fNEvents << std::endl;
    std::cout << "\t NSamples: " << nSamples << std::endl;

    std::cout << "[PedestalGenerator] Creating PedMaker" << std::endl;
    fPedMaker = new CTA::TargetCalib::PedestalMaker(fNModules, fNBlocks,
                                                    nSamples, diagnostic);
  }

  ~PedestalGenerator() {
    delete fReader;
    delete fPacket;
    delete fPedMaker;
  }

  int ProcessEvents(size_t maxEvents = 0) {
    size_t nEvents = fNEvents;
    if (maxEvents > 0 && maxEvents < nEvents) nEvents = maxEvents;

    std::cout << "[PedestalGenerator] Looping over " << nEvents
              << " events to determine pedestals" << std::endl;

    float progressL = 0.0;
    for (uint32_t iev = 0; iev < nEvents; ++iev) {
      uint32_t req_event = iev + fSkipEvents;

      fReader->GetEventHeader(req_event, fHeader);

      for (uint16_t ipack = 0; ipack < fNPacketsPerEvent; ipack++) {
        uint8_t *eventPacket = fReader->GetEventPacket(req_event, ipack);
        if (!eventPacket) {
          std::cout << "Event " << iev << " packet "
                    << ipack << " bad" << std::endl;
          return false;
        }
        fPacket->Assign(eventPacket, fPacketSize);
        uint8_t tm = fPacket->GetSlotID() - fFirstModule;
        uint16_t firstCellIdRaw = fPacket->GetFirstCellId();
        uint16_t firstCellId = (firstCellIdRaw + fSkipSamples) % fNCells;
        uint16_t row, column, blkPhase;
        CalculateRowColumnBlockPhase(firstCellId, row, column, blkPhase);
        auto block = (uint16_t) (row + column * N_ROWS);
        uint16_t nWaveforms = fPacket->GetNumberOfWaveforms();
        for (unsigned short iwav = 0; iwav < nWaveforms; iwav++) {
          fPacket->AssociateWaveform(iwav, fWf);
          uint16_t nSamples = fWf.GetSamples() - fSkipSamples - fSkipEndSamples;
          uint16_t tmpix = fWf.GetPixelID();
          for (unsigned short isam = 0; isam < nSamples; isam++) {
            unsigned short req_sam = isam + fSkipSamples;
            uint16_t adc = fWf.GetADC(req_sam);
            if (!fPedMaker->AddSample(adc, isam, tm, tmpix, block, blkPhase)) {
              std::cout << "Could not add " << adc << " to ped for tm " << tm
                        << " pix " << tmpix << std::endl;
              return false;
            }
          }
        }
      }
      float progress = (float) iev / nEvents;
      if ((progress - progressL) > 0.05) {
        PrintProgress(progress);
        progressL = progress;
      }
    }
    PrintProgress(1.0);
    std::cout << "\n";
    return 1;
  }

  int Save(std::string pedPath, bool compress) {
    std::cout << "Saving pedestals to: " << pedPath << std::endl;
    std::cout << "Compression = " << compress << std::endl;
    return fPedMaker->Save(pedPath, compress);
  }
};

}  // namespace TargetCalib
}  // namespace CTA

#endif //TARGETCALIB_PEDESTALGENERATOR_H
