//
// Created by Jason Watson on 08/05/2017.
//

#ifndef TARGETCALIB_TFGENERATOR_H
#define TARGETCALIB_TFGENERATOR_H

#include <iostream>
#include <fstream>
#include <vector>
#include <unistd.h>
#include <set>
#include <regex>

//TargetIO
#include "TargetIO/EventFileReader.h"

//TargetDriver
#include "TargetDriver/Waveform.h"
#include "TargetDriver/DataPacket.h"

//TargetCalib
#include "TargetCalib/TfMaker.h"
#include "TargetCalib/Calibrator.h"

typedef CTA::TargetIO::EventFileReader EventFileReader;

namespace CTA {
namespace TargetCalib {

class TfGenerator {
private:
  uint16_t fSkipSamples;
  uint16_t fSkipEndSamples;
  uint16_t fSkipEvents;
  uint16_t fSkipEndEvents;

  uint16_t fPacketSize;
  uint32_t fNPacketsPerEvent;
  CTA::TargetDriver::DataPacket* fPacket;
  CTA::TargetDriver::Waveform fWf;
  CTA::TargetDriver::EventHeader fHeader;

  std::vector<std::string> fEventPaths;
  std::vector<std::unique_ptr<EventFileReader>> fReaders;
  std::vector<float> fVpeds;
  std::vector<uint32_t> fNEventsV;
  CTA::TargetCalib::Calibrator* fCalibrator;
  CTA::TargetCalib::TfMaker* fTfMaker;

  size_t fNEvents = 0;
  uint16_t fNModules;
  uint8_t fFirstModule;
  uint16_t fNCells;
  uint16_t fNBlockSamples;
  uint16_t fNBlocks;
public:
  TfGenerator(std::vector<std::string> eventPaths,
              std::vector<float> vpedV, std::string pedestalPath,
              uint16_t maxEvents, uint16_t nCells,
              uint16_t skipSamples=0, uint16_t skipEndSamples=0,
              uint16_t skipEvents=0, uint16_t skipEndEvents=0) {

    fEventPaths = eventPaths;
    fNCells = nCells;
    fNBlockSamples = N_BLOCKPHASE;
    fNBlocks = fNCells / fNBlockSamples;
    fSkipSamples = skipSamples;
    fSkipEndSamples = skipEndSamples;
    fSkipEvents = skipEvents;
    fSkipEndEvents = skipEndEvents;

    std::cout << "[TfGenerator] Opening Event Files:" << std::endl;
    for (int i=0; i<fEventPaths.size(); ++i) {
      std::string path = fEventPaths[i];
      float vped = vpedV[i];
      std::unique_ptr<EventFileReader> reader(new EventFileReader(path));
      uint32_t nEvents = reader->GetNEvents() - fSkipEvents - fSkipEndEvents;
      uint32_t numEvents = nEvents > maxEvents && maxEvents > 0 ?
                           (uint32_t) maxEvents : nEvents;
      std::cout << "\tFile: " << path << "  NEvents: " << numEvents
                << "  Vped: " << vped << std::endl;
      fNEventsV.push_back(numEvents);
      fNEvents += numEvents;
      fReaders.push_back(std::move(reader));
    }
    fVpeds = vpedV;

    // Set information from first file
    fPacketSize = fReaders[0]->GetPacketSize();
    fNPacketsPerEvent = fReaders[0]->GetNPacketsPerEvent();
    fPacket = new CTA::TargetDriver::DataPacket(fPacketSize);

    // Get number of modules and first module id
    std::set<uint8_t> module_set;
    for (uint16_t ipack =0; ipack < fNPacketsPerEvent; ipack++) {
      uint8_t* eventPacket = fReaders[0]->GetEventPacket(0, ipack);
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

    // Get event/waveform information
    uint8_t* eventPacket = fReaders[0]->GetEventPacket(0, 0);
    fPacket->Assign(eventPacket, fPacketSize);
    fPacket->AssociateWaveform(0, fWf);
    uint16_t nSamples = fWf.GetSamples() - fSkipSamples - fSkipEndSamples;

    std::cout << "[TfGenerator] FIRST EVENT FILE CONTENTS: " << std::endl;
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
    std::cout << "\t NSamples: " << nSamples << std::endl;

    std::cout << "[TfGenerator] Creating Pedestal Calibrator"<< std::endl;
    fCalibrator = new CTA::TargetCalib::Calibrator(pedestalPath);
    std::cout << "[TfGenerator] Creating TfMaker"<< std::endl;
    fTfMaker = new CTA::TargetCalib::TfMaker(vpedV, fNModules, 64);
  }

  ~TfGenerator() {
    delete fPacket;
    delete fCalibrator;
    delete fTfMaker;
  }

  int EventProcessor(uint32_t ifile, uint32_t iev) {
    uint32_t req_event = iev + fSkipEvents;

    fReaders[ifile]->GetEventHeader(req_event, fHeader);

    for (uint16_t ipack = 0; ipack < fNPacketsPerEvent; ipack++) {
      uint8_t *eventPacket = fReaders[ifile]->GetEventPacket(req_event, ipack);
      if (!eventPacket) {
        std::cout << "Event " << iev << " packet "
                  << ipack << " bad" << std::endl;
        return false;
      }
      fPacket->Assign(eventPacket, fPacketSize);
      uint8_t tm = fPacket->GetSlotID() - fFirstModule;
      uint8_t row = fPacket->GetRow();
      uint8_t column = fPacket->GetColumn();
      uint8_t blockphase = fPacket->GetBlockPhase();
      fCalibrator->SetPacketInfo(tm, row, column, blockphase);
      auto fci = TargetDriver::DataPacket::CalculateFirstCellId(row, column, blockphase);
      uint16_t nWaveforms = fPacket->GetNumberOfWaveforms();
      for (unsigned short iwav = 0; iwav < nWaveforms; iwav++) {
        fPacket->AssociateWaveform(iwav, fWf);
        uint16_t nSamples = fWf.GetSamples() - fSkipSamples - fSkipEndSamples;
        uint16_t tmpix = fWf.GetPixelID();
        fCalibrator->SetLookupPosition(tm, tmpix);
        for (unsigned short isam = 0; isam < nSamples; isam++) {
          unsigned short req_sam = isam + fSkipSamples;
          uint16_t adc = fWf.GetADC(req_sam);
          float cval = fCalibrator->ApplySample(adc, req_sam);
          if (!fTfMaker->AddSample(cval, req_sam, tm, tmpix, fci)) {
            std::cout << "Could not add sample" << std::endl;
            return 0;
          }
        }
      }
    }
    return 1;
  }

  int ProcessEvents() {
    std::cout << "[TfGenerator] Looping over all files to "
              << "determine TF" << std::endl;

    uint32_t eventCounter = 0;
    float progressL = 0.0;
    for(uint32_t ifile=0; ifile<fReaders.size(); ++ifile) {
      fTfMaker->SetAmplitudeIndex(fVpeds[ifile]);
      for (uint32_t iev = 0; iev < fNEventsV[ifile]; ++iev) {
        if (!EventProcessor(ifile, iev)) {
          std::cout << "Could not process event " << iev << " from file "
                    << fEventPaths[ifile] << std::endl;
          return 0;
        }
        float progress = (float) eventCounter++ / (float) fNEvents;
        if ((progress - progressL) > 0.05) {
          PrintProgress(progress);
          progressL = progress;
        }
      }
    }
    PrintProgress(1.0);
    std::cout << "\n";
    return 1;
  }

  int Save(std::string tfPath, uint16_t adcStep, bool compress) {
    std::cout << "Saving TF to: " << tfPath << std::endl;
    std::cout << "ADC Step = " << adcStep << std::endl;
    std::cout << "Compression = " << compress << std::endl;
    return fTfMaker->Save(tfPath, adcStep, 0, 1050, compress);
  }
};

}  // namespace TargetCalib
}  // namespace CTA

#endif //TARGETCALIB_TFGENERATOR_H
