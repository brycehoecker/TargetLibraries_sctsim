/*
 Generate pedestal file from raw data
 Author - RW
*/

//TargetCalib
#include "TargetCalib/exe_classes/PedestalGenerator.h"

using namespace CTA::TargetCalib;

void ShowUsage(char *s);

int main(int argc, char** argv) {
  CTA::TargetCalib::FLog().ReportingLevel() = CTA::TargetCalib::sDebug;

  std::string dataFileName;
  std::string pedFilePath;
  int nEvents = 0;
  bool compress = false;
  bool diagnostic = false;
  bool checkForOutliers = false;
  float outlierNStd = 20.0;
  
  char tmp;
  if(argc == 1) {
    ShowUsage(argv[0]);
    exit(0);
  }

  while((tmp = (char) getopt(argc, argv, "hi:o:cn:dks:")) != -1) {
    switch(tmp) {
      case 'h':
        ShowUsage(argv[0]);
        exit(0);
 
      case 'i':
        dataFileName = optarg;
        pedFilePath = dataFileName.substr(0,dataFileName.find_last_of("_"));
        pedFilePath.append("_ped.tcal");
        break;
  
      case 'o':
        pedFilePath = optarg;
        break;

      case 'c':
        compress = true;
        break;
   
      case 'n':
        nEvents = std::stoi(optarg);
        break;

      case 'd':
        diagnostic = true;
        break;

//      case 'k':
//        checkForOutliers = true;
//        break;
//
//      case 's':
//        outlierNStd = std::stof(optarg);
//        break;
          
      default:
        ShowUsage(argv[0]);
        exit(0);
    }
  }
  std::cout<< "[main] Input file: "<< dataFileName << std::endl;
  std::cout<< "[main] Output file: "<<  pedFilePath << std::endl;
  std::cout<< "[main] Compress: "<< compress << std::endl;
  if (nEvents>0) std::cout<< "[main] Num Events: "<< nEvents << std::endl;
  std::cout<< "[main] Check for outliers: "<< checkForOutliers << std::endl;
  std::cout<< "[main] Outlier # std: "<< outlierNStd << std::endl;
  std::cout<< "[main] Diagnostic mode: "<< diagnostic << std::endl;

  if (!std::ifstream(dataFileName)) {
    std::cout << "Data file does not exist" << std::endl;
    return -1;
  }

  uint16_t nCells = N_STORAGECELL;

#ifdef CHECM
  uint16_t skipSamples = 32;
#else
  uint16_t skipSamples = 0;
#endif

  uint16_t skipEndSamples = 0;
  uint16_t skipEvents = 2;
  uint16_t skipEndEvents = 1;

  PedestalGenerator pedestalGenerator(dataFileName, nCells,
                                      skipSamples, skipEndSamples,
                                      skipEvents, skipEndEvents, diagnostic);

  if (!pedestalGenerator.ProcessEvents((size_t) nEvents)){
    std::cout << "Could not process data" << std::endl;
    return -1;
  }

  if (!pedestalGenerator.Save(pedFilePath, compress)) {
    std::cout << "Could not save pedestal data" << std::endl;
    return -1;
  }

  return 0;
}

void ShowUsage(char *s)
{
  std::cout<<"Purpose: Generate the pedestal file from a pedestal run."<<std::endl;
  std::cout<<"Usage:   "<<s<<" [-option] [argument]"<<std::endl;
  std::cout<<"option:  "<<"-h  Show help information"<<std::endl;
  std::cout<<"         "<<"-i  Raw data input file name"<<std::endl;
  std::cout<<"         "<<"-o  Pedestal output file name (optional)"<<std::endl;
  std::cout<<"         "<<"-c  Compress the output pedestal file? "
                                "Default = false (optional)"<<std::endl;
  std::cout<<"         "<<"-n  Number events to process (optional)"<<std::endl;
  std::cout<<"         "<<"-d  Save additional diagnostic tables (hits and "
                                "stddev) Default = false (optional)"<<std::endl;
  std::cout<<"example: "<<s<<" -i /path/Run00001_r0.tio"<<std::endl;
}
