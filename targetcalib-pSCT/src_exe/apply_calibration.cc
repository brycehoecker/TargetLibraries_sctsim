/*
 Apply calibration to raw data

*/

#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <unistd.h>
#include <set>

//TargetIO
#include "TargetIO/EventFileReader.h"
#include "TargetIO/EventFileWriter.h"

//TargetCalib
#include "TargetCalib/Calibrator.h"
#include "TargetCalib/CalibratorMultiFile.h"

using namespace CTA::TargetCalib;

void ShowUsage(char *s);

class CalibratorConstructor {
private:
  CTA::TargetCalib::Calibrator* fCalibrator = nullptr;

  std::string fPedPath;
  std::string fTfPath;
  std::vector<std::string> fTfAutoPaths;
  bool fTfAuto;

  float fOffset = 0;
  float fScale = 1;

public:
  CalibratorConstructor(
    std::string pedPath,
    std::string tfPath,
    bool tfAuto
  ) :
    fPedPath(std::move(pedPath)),
    fTfPath(std::move(tfPath)),
    fTfAuto(tfAuto){}

  ~CalibratorConstructor() {
    delete fCalibrator;
  }

  CTA::TargetCalib::Calibrator* GetCalibrator(
    uint16_t nModules,
    uint16_t firstModule,
    CTA::TargetIO::EventFileReader* reader
  ) {
    if (fCalibrator)
      return fCalibrator;

    std::cout << "[CalibratorConstructor] Creating Calibrator" << std::endl;
    bool tfPathExists = false;
    if (fTfAuto) {
      fTfPath = "auto";
      std::vector<int16_t> SNs(nModules);
      for (uint16_t tm = firstModule; tm < nModules + firstModule; ++tm) {
        SNs[tm] = reader->GetSN(tm);
      }
      fCalibrator = new CalibratorMultiFile(fPedPath, SNs);
    } else {
      if (!fTfPath.empty()) tfPathExists = true;
      fCalibrator = new Calibrator(fPedPath, fTfPath);
    }

    // Decide on scale and offset
    if (!fPedPath.empty() && !tfPathExists) {
      // Expects sample range of -700 to 4096
      fOffset = 700;
      fScale = 13.6;
    } else if (!fPedPath.empty() && tfPathExists) {
      // Expects sample range of -370 to 2500
      fOffset = 370;
      fScale = 22.8;
    } else {
      std::cout << "WARNING: No case found for setting Offset and Scale"
                << std::endl;
    }
    std::cout << "[CalibratorConstructor] Offset = " << fOffset
              << ", Scale = " << fScale << std::endl;

    return fCalibrator;
  }

  std::string GetPedPath() { return fPedPath;}
  std::string GetTfPath() { return fTfPath;}
  float GetOffset() { return fOffset;}
  float GetScale() { return fScale;}
};


class CalibrationApplier {
private:
  uint16_t fPacketSize;
  uint32_t fNPacketsPerEvent;
  CTA::TargetIO::EventFileReader* fReader = nullptr;
  CTA::TargetDriver::DataPacket* fPacket = nullptr;
  CTA::TargetDriver::EventHeader* fHeader = nullptr;
  CTA::TargetDriver::Waveform fWf;

  CTA::TargetIO::EventFileWriter* fWriter = nullptr;
  CTA::TargetDriver::RawEvent* fRawEvent = nullptr;

  CalibratorConstructor* fCalibConstructor = nullptr;

  size_t fNEvents;
  uint16_t fNModules;
  uint8_t fFirstModule;
  uint16_t fNCells;
  uint16_t fNBlockSamples;
  uint16_t fNBlocks;
  uint16_t fSkipSamples;
public:
  CalibrationApplier(
    const std::string &r0Path, const std::string &r1Path,
    CalibratorConstructor* calibConstructor,
    uint16_t nCells, uint16_t skipSamples)
    : fCalibConstructor(calibConstructor)
  {

    std::cout << "[CalibrationApplier] Opening R0 Event File: "
              << r0Path << std::endl;
    fReader = new CTA::TargetIO::EventFileReader(r0Path);
    fPacketSize = fReader->GetPacketSize();
    fNPacketsPerEvent = fReader->GetNPacketsPerEvent();
    fPacket = new CTA::TargetDriver::DataPacket(fPacketSize);

    // Get number of modules and first module id
    std::set<uint8_t> module_set;
    for (uint16_t ipack = 0; ipack < fNPacketsPerEvent; ipack++) {
      uint8_t* eventPacket = fReader->GetEventPacket(0, ipack);
      fPacket->Assign(eventPacket, fPacketSize);
#ifndef SCT
      uint8_t module = fPacket->GetSlotID();
      module_set.insert(module);
#endif
    }
#ifdef SCT
    for (uint8_t module = 0; module < 24; module++) {
      module_set.insert(module);
    }
#endif
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
    fNEvents = fReader->GetNEvents();
    fSkipSamples = skipSamples;

    // Get event/waveform information
    uint8_t* eventPacket = fReader->GetEventPacket(0, 0);
    fPacket->Assign(eventPacket, fPacketSize);
    fPacket->AssociateWaveform(0, fWf);
    uint16_t nSamples = fWf.GetSamples() - fSkipSamples;

    std::cout << "[CalibrationApplier] EVENT FILE CONTENTS: " << std::endl;
    std::cout << "\t NModules: " << fNModules << std::endl;
    std::cout << "\t ActiveModuleSlots: ";
    for (uint8_t slot: module_set) {
      std::cout << (unsigned) slot << " ";
    }
    std::cout << std::endl;
    std::cout << "\t NCells: " << fNCells << std::endl;
    std::cout << "\t NBlockSamples: " << fNBlockSamples << std::endl;
    std::cout << "\t NBlocks: " << fNBlocks << std::endl;
    std::cout << "\t NEvents: " << fNEvents << std::endl;
    std::cout << "\t NSamples: " << nSamples << std::endl;
    std::cout << "\t SkipSamples: " << fSkipSamples << std::endl;

    std::cout << "[CalibrationApplier] Creating R1 Writer"<< std::endl;
    fWriter = new CTA::TargetIO::EventFileWriter(r1Path, fReader);
    fRawEvent = new CTA::TargetDriver::RawEvent((uint16_t) fNPacketsPerEvent,
                                                fPacketSize);

  }

  ~CalibrationApplier() {
    delete fReader;
    delete fPacket;
    delete fWriter;
    delete fRawEvent;
  }

  static void PrintProgress(float progress = 0.0) {
    int barWidth = 70;
    std::cout << "[";
    auto pos = int(barWidth * progress);
    for (int i = 0; i < barWidth; ++i) {
      if (i < pos) std::cout << "=";
      else if (i == pos) std::cout << ">";
      else std::cout << " ";
    }
    std::cout << "] " << int(progress * 100.0) << " %\r";
    std::cout.flush();
  }

  int ProcessEvents(size_t maxEvents=0, size_t nLastEvents=0) {

    CTA::TargetCalib::Calibrator* calibrator = fCalibConstructor->
      GetCalibrator(fNModules, fFirstModule, fReader);
    float offset = fCalibConstructor->GetOffset();
    float scale = fCalibConstructor->GetScale();

    uint32_t startingEvent = 0;
    size_t nEvents = fNEvents;
    if (maxEvents>0 && maxEvents<nEvents) nEvents = maxEvents;
    if (nLastEvents>0 && nLastEvents < nEvents) {
      startingEvent = (uint32_t) (nEvents - nLastEvents);
      std::cout << "[CalibrationApplier] Starting from event " << startingEvent
                << std::endl;
    }
    size_t totalEvents = nEvents - startingEvent;

    std::cout << "[CalibrationApplier] Looping over " << totalEvents
              << " events to perform R1 calibration" << std::endl;

    std::chrono::steady_clock::time_point t0 = std::chrono::steady_clock::now();
    float progressL = 0.0;
    for (uint32_t iev = startingEvent; iev < nEvents; ++iev) {
      fRawEvent->Clear();
      for (uint16_t ipack = 0; ipack < fNPacketsPerEvent; ipack++) {
        uint8_t *eventPacket = fReader->GetEventPacket(iev, ipack);
        if (!eventPacket) {
          std::cout << "Event " << iev << " packet "
                    << ipack << " bad" << std::endl;
          return false;
        }
        fPacket->Assign(eventPacket, fPacketSize);
#ifdef SCT
        uint8_t tm = fPacket->GetDetectorID() - fFirstModule;
#else
        uint8_t tm = fPacket->GetSlotID() - fFirstModule;
#endif
#ifdef CHECM
        uint16_t firstCellIdRaw = fPacket->GetFirstCellId();
        uint16_t firstCellId = (firstCellIdRaw + fSkipSamples) % fNCells;
        uint16_t row, column, blockphase;
        CalculateRowColumnBlockPhase(firstCellId, row, column, blockphase);
#else
        uint8_t row = fPacket->GetRow();
        uint8_t column = fPacket->GetColumn();
        uint8_t blockphase = fPacket->GetBlockPhase();
#endif
        calibrator->SetPacketInfo(tm, row, column, blockphase);
        uint16_t nWaveforms = fPacket->GetNumberOfWaveforms();
        for (unsigned short iwav = 0; iwav < nWaveforms; iwav++) {
          fPacket->AssociateWaveform(iwav, fWf);
          uint16_t nSamples = fWf.GetSamples() - fSkipSamples;
          uint16_t tmpix = fWf.GetPixelID();
          calibrator->SetLookupPosition(tm, tmpix);
          for (unsigned short isam = 0; isam < nSamples; isam++) {
            unsigned short req_sam = isam + fSkipSamples;
            uint16_t adc = fWf.GetADC(req_sam);
            float cval = calibrator->ApplySample(adc, isam);
            fWf.SetADC16bit(req_sam, (uint16_t)round((cval + offset) * scale));
          }
        }
        fRawEvent->AddNewPacket(eventPacket, ipack, fPacketSize);
      }
      // Copy event header and store event
      fHeader = &fRawEvent->GetEventHeader();
      fReader->GetEventHeader(iev,*fHeader);
      fWriter->AddEvent(fRawEvent);

      float progress = (float) (iev - startingEvent) / totalEvents;
      if ((progress-progressL)>0.05) {
        PrintProgress(progress);
        progressL = progress;
      }
    }
    PrintProgress(1.0);
    std::cout << "\n";

    std::chrono::steady_clock::time_point t1 = std::chrono::steady_clock::now();
    double dt = std::chrono::duration_cast<std::chrono::nanoseconds> (t1-t0).count() * 1e-9;
    std::cout << "Time to process events: " << std::setprecision(3)
              << dt << " seconds ("<< (double) totalEvents/dt
              << " Hz)"<< std::endl;

    return 1;
  }

  void WriteHeader() {
    std::string pedPath = fCalibConstructor->GetPedPath();
    std::string tfPath = fCalibConstructor->GetTfPath();
    float offset = fCalibConstructor->GetOffset();
    float scale = fCalibConstructor->GetScale();

    std::cout << "[CalibrationApplier] Adding calibration keys "
      "to writer header" << std::endl;
    fWriter->AddCardImage("R1", true, "If true, then r1 calibration has "
                                      "been applied to these events");
    fWriter->AddCardImage("PEDESTAL", pedPath, "Pedestal file used on data");
    fWriter->AddCardImage("TF", tfPath, "Transfer Function file used on data");
    fWriter->AddCardImage("OFFSET", offset, "Offset of the stored data");
    fWriter->AddCardImage("SCALE", scale, "Scale of the stored data");
  }

};

int main(int argc, char** argv) {

  std::vector<std::string> r0FilePaths;
  std::vector<std::string> r1FilePaths;
  std::string pedFilePath, tfFilePath;
  int nEvents = -1;
  int nLastEvents = -1;
  bool autoTF = false;
  int index;
  std::string next;

  char tmp;
  if(argc == 1) {
    ShowUsage(argv[0]);
    exit(0);
  }

  while((tmp = (char) getopt(argc, argv, "hi:o:p:t:xn:m:")) != -1) {
    switch(tmp) {
      case 'h':
        ShowUsage(argv[0]);
        exit(0);

      case 'i':
        index = optind-1;
        while(index < argc){
          next = strdup(argv[index]);
          index++;
          if(next[0] != '-'){
            r0FilePaths.push_back(next);
          }
          else break;
        }
        optind = index - 1;
        break;

      case 'o':
        index = optind-1;
        while(index < argc){
          next = strdup(argv[index]);
          index++;
          if(next[0] != '-'){
            r1FilePaths.push_back(next);
          }
          else break;
        }
        optind = index - 1;
        break;

      case 'p':
        pedFilePath = optarg;
        break;

      case 't':
        tfFilePath = optarg;
        break;

      case 'x':
        autoTF = true;
        break;

      case 'n':
        nEvents = std::stoi(optarg);
        break;

      case 'm':
        nLastEvents = std::stoi(optarg);
        break;

      default:
        ShowUsage(argv[0]);
        exit(0);
    }
  }

  if (r0FilePaths.empty()) {
    std::cout << "ERROR: Raw data file required" << std::endl;
    return -1;
  }

  if (r1FilePaths.empty()) {
    for (auto path : r0FilePaths) {
      std::string r1FilePath = path.substr(0, path.find_last_of("r0") - 1);
      r1FilePath.append("r1.tio");
      r1FilePaths.push_back(r1FilePath);
    }
  }

  if (r0FilePaths.size() != r1FilePaths.size()) {
    std::cout << "ERROR: An equal amount of input and "
                 "output paths need to be specified" << std::endl;
    return -1;
  }

  for (auto path : r0FilePaths) {
    if (!std::ifstream(path)) {
      std::cout << "ERROR: Raw data file does not exist: " << path << std::endl;
      return -1;
    }
  }

  if (pedFilePath.empty()) {
    std::cout << "ERROR: Pedestal file required" << std::endl;
    return -1;
  }

  if (!std::ifstream(pedFilePath)) {
    std::cout << "ERROR: Pedestal file does not exist" << std::endl;
    return -1;
  }

  if (!tfFilePath.empty() && !std::ifstream(tfFilePath)) {
    std::cout << "ERROR: Transfer function file does not exist" << std::endl;
    return -1;
  }

  uint16_t nCells = N_STORAGECELL;

#ifdef CHECM
  uint16_t skipSamples = 32;
#else
  uint16_t skipSamples = 0;
#endif

  CalibratorConstructor calibratorConstructor(pedFilePath, tfFilePath, autoTF);


  for (int ipath=0; ipath<r0FilePaths.size(); ++ipath) {
    std::cout << "[main] Calibrating file " << ipath + 1
              << "/" << r0FilePaths.size() << std::endl;
    std::string r0Path = r0FilePaths[ipath];
    std::string r1Path = r1FilePaths[ipath];

    std::cout << "[main] Input file: " << r0Path << std::endl;
    std::cout << "[main] Output file: " << r1Path << std::endl;
    if (nEvents > 0) std::cout << "[main] Num Events: " << nEvents << std::endl;

    if (std::ifstream(r1Path)) {
      std::cout << "[main] WARNING: calibrated data file already exists, "
                << "deleting file..." << std::endl;
      std::remove(r1Path.c_str());
    }

    CalibrationApplier calibrationApplier(r0Path, r1Path,
                                          &calibratorConstructor, nCells,
                                          skipSamples);

    if (!calibrationApplier.ProcessEvents((size_t) nEvents,
                                          (size_t) nLastEvents)) {
      std::cout << "Could not process data" << std::endl;
      return -1;
    }

    calibrationApplier.WriteHeader();
  }

  return 0;
}

void ShowUsage(char *s)
{
  std::cout<<"Purpose: Create a new tio file containing calibrated waveforms."<<std::endl;
  std::cout<<"         This version takes a TF file to calibrate all modules."<<std::endl;
  std::cout<<"Usage:   "<<s<<" [-option] [argument]"<<std::endl;
  std::cout<<"option:  "<<"-h  Show help information"<<std::endl;
  std::cout<<"         "<<"-i  Raw data input file name(s)"<<std::endl;
  std::cout<<"         "<<"-o  R1 output file name(s)"<<std::endl;
  std::cout<<"         "<<"-p  Pedestal file name (required)"<<std::endl;
  std::cout<<"         "<<"-t  Transfer function file name (optional)"<<std::endl;
  std::cout<<"         "<<"-x  Automatically get transfer function file from header (flag)"<<std::endl;
  std::cout<<"         "<<"-n  Number events to process (optional)"<<std::endl;
  std::cout<<"         "<<"-m  Process only the last m events(optional)"<<std::endl;
}
