//
// Created by Jason Watson on 25/10/2017.
//

#include <iostream>
#include <fstream>
#include <vector>
#include <unistd.h>
#include <set>

#include "TargetCalib/Calibrator.h"

using namespace CTA::TargetCalib;

void ShowUsage(char *s);

int main(int argc, char **argv) {

  std::string inFilePath;
  std::string outFilePath;

  char tmp;
  if (argc == 1) {
    ShowUsage(argv[0]);
    exit(0);
  }

  while ((tmp = (char) getopt(argc, argv, "hi:o:")) != -1) {
    switch (tmp) {
      case 'h':
        ShowUsage(argv[0]);
        exit(0);

      case 'i':
        inFilePath = optarg;
        break;

      case 'o':
        outFilePath = optarg;
        break;

      default:
        ShowUsage(argv[0]);
        exit(0);
    }
  }
  std::cout << "[main] Input file: " << inFilePath << std::endl;
  std::cout << "[main] Output file: " << outFilePath << std::endl;

  if (inFilePath.empty()) {
    std::cout << "Input filepath required" << std::endl;
    return -1;
  }

  if (outFilePath.empty()) {
    std::cout << "Output filepath required" << std::endl;
    return -1;
  }

  if (std::ifstream(outFilePath)) {
    std::cout << "[main] Error: output filepath already exists" << std::endl;
    return -1;
  }

  auto *cr = new CTA::TargetCalib::CalibReadWriter();
  auto *cw = new CTA::TargetCalib::CalibReadWriter();

  vector4_float tf;
  std::vector<int32_t> adcSteps;

  if(cr->ReadTfData(inFilePath, adcSteps, tf)!=TCAL_FILE_OK) {
    std::cout << "Could not load transfer function file:" << inFilePath << std::endl;
    return false;
  }

  for (uint16_t tm=0; tm<tf.size(); ++tm) {
    auto tf_tm = tf[tm];
    for (uint16_t tmpix=0; tmpix<tf_tm.size(); ++tmpix) {
      auto tf_tmpix = tf_tm[tmpix];
      for (uint16_t cell=0; cell<tf_tmpix.size(); ++cell) {
        auto tf_cell = tf_tmpix[cell];
        for (size_t pnt=0; pnt<tf_cell.size(); ++pnt) {
          tf[tm][tmpix][cell][pnt] -= 180;
        }
      }
    }
  }

  std::cout << "Writing File" << std::endl;
  int status = cw->WriteTfData(outFilePath, adcSteps, tf, false);
  if (status != TCAL_FILE_OK) {
    std::cout << "Error Saving Tf File: " << status << std::endl;
  }

  delete cr;
  delete cw;

  return 0;
}

void ShowUsage(char *s) {
  std::cout
    << "Purpose: Apply the offset fix to the TF file and create a new tf.tcal."
    << std::endl;
  std::cout << "Usage:   " << s << " [-option] [argument]" << std::endl;
  std::cout << "option:  " << "-h  Show help information" << std::endl;
  std::cout << "         " << "-i  Input TF filepath" << std::endl;
  std::cout << "         " << "-o  Output TF filepath" << std::endl;
}
