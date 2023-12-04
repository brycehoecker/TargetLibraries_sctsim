//
// Generate Transfer Function file
// Created by Jason Watson on 23/01/2017.
//

//TargetCalib
#include "TargetCalib/exe_classes/TfGenerator.h"

using namespace CTA::TargetCalib;

void ShowUsage(char *s);

int main(int argc, char** argv) {
  CTA::TargetCalib::FLog().ReportingLevel() = CTA::TargetCalib::sDebug;

  std::string configPath = "";
  std::string pedestalPath = "";
  std::string tfFilePath = "";
  bool compress = false;
  uint16_t maxEvents = 0;
  uint16_t adcStep = 8;

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
        configPath = optarg;
        break;

      case 'p':
        pedestalPath = optarg;
        break;

      case 'o':
        tfFilePath = optarg;
        break;

      case 'c':
        compress = true;
        break;

      case 'n':
        maxEvents = (uint16_t) std::stoi(optarg);
        break;

      case 'a':
        adcStep = (uint16_t) std::stoi(optarg);
        break;

      default:
        ShowUsage(argv[0]);
        exit(0);
    }
  }

  if (configPath.empty()) {
    std::cout << "No input config file specified" << std::endl;
    return -1;
  }

  if (pedestalPath.empty()) {
    std::cout << "No pedestal file specified" << std::endl;
    return -1;
  }

  if (tfFilePath.empty()) {
      std::cout << "No output path specified" << std::endl;
      return -1;
  }

  std::cout << "[main] Reading config file" << std::endl;
  std::ifstream configFile(configPath);
  std::string path;
  float vped;
  std::vector<std::string> eventPaths;
  std::vector<float > vpedV;
  while (configFile >> path >> vped)
  {
    if (!std::ifstream(path)) {
      std::cout << "Skipping non-existent file: " << path << std::endl;
      continue;
    }
    eventPaths.push_back(path);
    vpedV.push_back(vped);
  }

  std::cout<< "[main] Config file: "<< configPath << std::endl;
  std::cout<< "[main] Pedestal file: "<< pedestalPath << std::endl;
  std::cout<< "[main] Output file: "<<  tfFilePath << std::endl;
  std::cout<< "[main] Compress: "<< compress << std::endl;
  if (maxEvents>0) std::cout<< "[main] Max Events: "<< maxEvents << std::endl;
  std::cout<< "[main] ADC step: "<< adcStep << std::endl;

  std::cout << "[main] Number of valid files: " << eventPaths.size()
            << std::endl;
  if (eventPaths.size() == 0)
    return -1;

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

  TfGenerator tfGenerator(eventPaths, vpedV, pedestalPath,
                          maxEvents, nCells,
                          skipSamples, skipEndSamples,
                          skipEvents, skipEndEvents);

  if (!tfGenerator.ProcessEvents()) {
    std::cout << "Could not process data" << std::endl;
    return -1;
  }

  if (!tfGenerator.Save(tfFilePath, adcStep, compress)) {
    std::cout << "Could not save tf data" << std::endl;
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
  std::cout << "         " << "-o  TF output file path (required)" << std::endl;
  std::cout << "         " << "-n  Number events to process in each file (optional)" << std::endl;
  std::cout << "         " << "-a  ADC step to store TF in (Default=8)" << std::endl;
  std::cout << "example: " << s <<" -i /path/to/config.txr -p /path/to/pedestal" << std::endl;
}
