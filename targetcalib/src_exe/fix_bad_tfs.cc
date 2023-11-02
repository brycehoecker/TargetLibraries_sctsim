//
// Created by Jason Watson on 25/10/2017.
//

#include <iostream>
#include <fstream>
#include <vector>
#include <unistd.h>
#include <set>
#include <algorithm>

#include "TargetCalib/Calibrator.h"

using namespace CTA::TargetCalib;

void ShowUsage(char *s);

int main(int argc, char **argv) {

  std::string inFilePath;
  std::string outFilePath;

  char tmp;
//  if (argc == 1) {
//    ShowUsage(argv[0]);
//    exit(0);
//  }

  while ((tmp = (char) getopt(argc, argv, "h")) != -1) {
    switch (tmp) {
      case 'h':
        ShowUsage(argv[0]);
        exit(0);

      default:
        ShowUsage(argv[0]);
        exit(0);
    }
  }

  std::string dir = std::getenv("TC_CONFIG_PATH");
  std::string inFileBase = dir + "/SN%04d_tf.tcal";
  std::string outFileBase = dir + "/SN%04d_tf_fix.tcal";
  uint64_t nChar = inFileBase.length() + 10;

  std::vector<int> SNs = {25, 61, 74};
  std::vector<std::vector<int>> bad_channels_all = {
    {5, 6, 10},
    {42},
    {56, 57, 58}
  };

  for (int i=0; i<SNs.size(); ++i) {
    int sn = SNs[i];
    std::vector<int> bad_channels = bad_channels_all[i];
    char pathIn[nChar];
    char pathOut[nChar];
    sprintf(pathIn, inFileBase.c_str(), sn);
    sprintf(pathOut, outFileBase.c_str(), sn);
    inFilePath = std::string(pathIn);
    outFilePath = std::string(pathOut);

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

    if (cr->ReadTfData(inFilePath, adcSteps, tf) != TCAL_FILE_OK) {
      std::cout << "Could not load transfer function file:" << inFilePath
                << std::endl;
      return false;
    }

    // Create average for ASIC
    vector4_float tfSum( tf.size(), vector3_float(tf[0].size(), vector2_float(
      4, std::vector<float>(tf[0][0][0].size(), 0))));
    vector4_float tfN(tf.size(), vector3_float(tf[0].size(), vector2_float(
      4, std::vector<float>(tf[0][0][0].size(),0))));
    for (uint16_t tm = 0; tm < tf.size(); ++tm) {
      auto tf_tm = tf[tm];
      for (uint16_t tmpix = 0; tmpix < tf_tm.size(); ++tmpix) {
        if (std::find(bad_channels.begin(), bad_channels.end(), tmpix) !=
            bad_channels.end())
          continue;
        auto asic = tmpix / 16;
        auto tf_tmpix = tf_tm[tmpix];
//      std::cout << asic << " " << tmpix << std::endl;
        for (uint16_t cell = 0; cell < tf_tmpix.size(); ++cell) {
          auto tf_cell = tf_tmpix[cell];
          for (size_t pnt = 0; pnt < tf_cell.size(); ++pnt) {
            tfSum[tm][asic][cell][pnt] += tf[tm][tmpix][cell][pnt];
            tfN[tm][asic][cell][pnt] += 1;
          }
        }
      }
    }

    // Fix bad channels
    for (uint16_t tm = 0; tm < tf.size(); ++tm) {
      auto tf_tm = tf[tm];
      for (auto tmpix : bad_channels) {
        auto asic = tmpix / 16;
        auto tf_tmpix = tf_tm[tmpix];
        for (uint16_t cell = 0; cell < tf_tmpix.size(); ++cell) {
          auto tf_cell = tf_tmpix[cell];
          for (size_t pnt = 0; pnt < tf_cell.size(); ++pnt) {
            tf[tm][tmpix][cell][pnt] =
              tfSum[tm][asic][cell][pnt] / tfN[tm][asic][cell][pnt];
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
  }
  return 0;
}

void ShowUsage(char *s) {
  std::cout
    << "Purpose: Fix the bad channel's TFs using the average for its asic"
    << std::endl;
  std::cout << "Usage:   " << s << " [-option] [argument]" << std::endl;
  std::cout << "option:  " << "-h  Show help information" << std::endl;
  std::cout << "         " << "-i  Input TF filepath" << std::endl;
  std::cout << "         " << "-o  Output TF filepath" << std::endl;
}
