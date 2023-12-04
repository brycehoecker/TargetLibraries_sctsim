#include <iostream>
#include <fstream>
#include <vector>
#include <unistd.h>
#include <set>
#include <regex>

//TargetIO
#include "TargetIO/EventFileReader.h"

//TargetDriver
#include "TargetDriver/DataPacket.h"

//TargetCalib
#include "TargetCalib/TfMaker.h"
#include "TargetCalib/Calibrator.h"

using namespace CTA::TargetCalib;
typedef CTA::TargetIO::EventFileReader EventFileReader;

void ShowUsage(char *s);

namespace CTA {
namespace TargetCalib {

class PedestalTfGenerator {
private:
  uint16_t fSkipSamples;
  uint16_t fSkipEndSamples;
  uint16_t fSkipEvents;
  uint16_t fSkipEndEvents;

  uint16_t fPacketSize;
  uint32_t fNPacketsPerEvent;
  CTA::TargetDriver::DataPacket* fPacket;
  CTA::TargetDriver::Waveform fWf;

  EventFileReader* fReader;
  CTA::TargetCalib::Calibrator* fCalibrator;
  CTA::TargetCalib::TfMaker* fTfMaker;

  size_t fNEvents = 0;
  uint16_t fNModules;
  uint8_t fFirstModule;
  uint16_t fNCells;
  uint16_t fNBlockSamples;
  uint16_t fNBlocks;
public:
  PedestalTfGenerator(const std::string &r0Path, std::string pedestalPath,
                      uint16_t nCells,
                      uint16_t skipSamples=0, uint16_t skipEndSamples=0,
                      uint16_t skipEvents=0, uint16_t skipEndEvents=0) {

    fNCells = nCells;
    fNBlockSamples = N_BLOCKPHASE;
    fNBlocks = fNCells / fNBlockSamples;
    fSkipSamples = skipSamples;
    fSkipEndSamples = skipEndSamples;
    fSkipEvents = skipEvents;
    fSkipEndEvents = skipEndEvents;

    fReader = new EventFileReader(r0Path);
    fNEvents = fReader->GetNEvents() - fSkipEvents - fSkipEndEvents;
    fPacketSize = fReader->GetPacketSize();
    fNPacketsPerEvent = fReader->GetNPacketsPerEvent();
    fPacket = new CTA::TargetDriver::DataPacket(fPacketSize);

    // Get number of modules and first module id
    std::set<uint8_t> module_set;
    for (uint16_t ipack =0; ipack < fNPacketsPerEvent; ipack++) {
      uint8_t* eventPacket = fReader->GetEventPacket(0, ipack);
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
    uint8_t* eventPacket = fReader->GetEventPacket(0, 0);
    fPacket->Assign(eventPacket, fPacketSize);
    fPacket->AssociateWaveform(0, fWf);
    uint16_t nSamples = fWf.GetSamples() - fSkipSamples - fSkipEndSamples;

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
    fCalibrator = new CTA::TargetCalib::Calibrator(std::move(pedestalPath));
    std::cout << "[TfGenerator] Creating TfMaker"<< std::endl;
    fTfMaker = new CTA::TargetCalib::TfMaker({0}, fNModules, nCells);
  }

  ~PedestalTfGenerator() {
    delete fReader;
    delete fPacket;
    delete fCalibrator;
    delete fTfMaker;
  }

  static void PrintProgress(float progress = 0.0) {
    int barWidth = 70;
    std::cout << "[";
    auto pos = (int) (barWidth * progress);
    for (int i = 0; i < barWidth; ++i) {
      if (i < pos) std::cout << "=";
      else if (i == pos) std::cout << ">";
      else std::cout << " ";
    }
    std::cout << "] " << int(progress * 100.0) << " %\r";
    std::cout.flush();
  }

  int ProcessEvents() {
    std::cout << "[TfGenerator] Looping over all files to "
              << "determine TF" << std::endl;

    uint32_t eventCounter = 0;
    float progressL = 0.0;
    fTfMaker->SetAmplitudeIndex(0);
    for (uint32_t iev = 0; iev < fNEvents; ++iev) {
      uint32_t req_event = iev + fSkipEvents;
      for (uint16_t ipack = 0; ipack < fNPacketsPerEvent; ipack++) {
        uint8_t *eventPacket = fReader->GetEventPacket(req_event, ipack);
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
      float progress = (float) eventCounter++ / (float) fNEvents;
      if ((progress - progressL) > 0.05) {
        PrintProgress(progress);
        progressL = progress;
      }
    }
    PrintProgress(1.0);
    std::cout << "\n";
    return 1;
  }

  int Save(const std::string &output_path) {
    std::cout << "Saving TFInput to: " << output_path << std::endl;
    return fTfMaker->SaveTfInput(output_path);
  }
};

}}

int main(int argc, char** argv) {
  CTA::TargetCalib::FLog().ReportingLevel() = CTA::TargetCalib::sDebug;

  std::string r0Path;
  std::string pedestalPath;
  std::string outputPath;

  char tmp;
  if(argc == 1) {
    ShowUsage(argv[0]);
    exit(0);
  }

  while((tmp = (char) getopt(argc, argv, "hi:s:f:p:o:cn:a:")) != -1) {
    switch(tmp) {
      case 'h':
        ShowUsage(argv[0]);
        exit(0);

      case 'i':
        r0Path = optarg;
        break;

      case 'p':
        pedestalPath = optarg;
        break;

      case 'o':
        outputPath = optarg;
        break;

      default:
        ShowUsage(argv[0]);
        exit(0);
    }
  }

  if (r0Path.empty()) {
    std::cout << "No input r0 file specified" << std::endl;
    return -1;
  }

  if (pedestalPath.empty()) {
    std::cout << "No pedestal file specified" << std::endl;
    return -1;
  }

  if (outputPath.empty()) {
    std::cout << "No output file specified" << std::endl;
    return -1;
  }

  std::cout<< "[main] Input file: "<< r0Path << std::endl;
  std::cout<< "[main] Pedestal file: "<< pedestalPath << std::endl;
  std::cout<< "[main] Output file: "<<  outputPath << std::endl;

#ifdef CHECS
  uint16_t nCells = 4096;
#else
  uint16_t nCells = 16384;
#endif

#ifdef CHECM
  uint16_t skipSamples = 32;
#else
  uint16_t skipSamples = 0;
#endif

  uint16_t skipEndSamples = 0;
  uint16_t skipEvents = 2;
  uint16_t skipEndEvents = 1;

  PedestalTfGenerator tfGenerator(r0Path, pedestalPath, nCells,
                                  skipSamples, skipEndSamples,
                                  skipEvents, skipEndEvents);

  if (!tfGenerator.ProcessEvents()) {
    std::cout << "Could not process data" << std::endl;
    return -1;
  }

  if (!tfGenerator.Save(outputPath)) {
    std::cout << "Could not save tfinput data" << std::endl;
    return -1;
  }

  return 0;
}

void ShowUsage(char *s)
{
  std::cout<<"Purpose: Generate the TF file from a list of TF runs."<<std::endl;
  std::cout<<"         This version assumes 16384 cells."<<std::endl;
  std::cout << "Usage:   " << s <<" [-option] [argument]" << std::endl;
  std::cout << "option:  " << "-h  Show help information" << std::endl;
  std::cout << "         " << "-i  Config input path (required). Expects column layout: [run filepath] [vped]" << std::endl;
  std::cout << "         " << "-p  Pedestal file path (required)" << std::endl;
  std::cout << "         " << "-o  TF output file path (optional)" << std::endl;
  std::cout << "         " << "-n  Number events to process in each file (optional)" << std::endl;
  std::cout << "         " << "-a  ADC step to store TF in (Default=8)" << std::endl;
  std::cout << "example: " << s <<" -i /path/to/config.txr -p /path/to/pedestal" << std::endl;
}
