// Copyright (c) 2016 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Extract the array directly from the file for plotting and debugging
 purposes
 */

#pragma clang diagnostic push
#pragma ide diagnostic ignored "OCUnusedGlobalDeclarationInspection"
#pragma ide diagnostic ignored "OCUnusedStructInspection"
#ifndef INCLUDE_TARGETCALIB_CALIBARRAYREADER_H_
#define INCLUDE_TARGETCALIB_CALIBARRAYREADER_H_

#include <vector>

#include "TargetCalib/CalibReadWriter.h"
#include "TargetCalib/Constants.h"
#include "TargetCalib/Logger.h"
#include "TargetCalib/Utils.h"

namespace CTA {
namespace TargetCalib {

class PedestalArrayReader {
private:
  CalibReadWriter fRW;
  vector4_float fPedestal;
  vector4_float fHits;
  vector4_float fStd;

public:
  explicit PedestalArrayReader(const std::string& filePath) {
    fRW.ReadPedestalData(filePath, fPedestal, fHits, fStd);
  }

  std::vector<std::vector<std::vector<std::vector<float>>>> GetPedestal() {
    return fPedestal;
  }
  std::vector<std::vector<std::vector<std::vector<float>>>> GetHits() {
    return fHits;
  }
  std::vector<std::vector<std::vector<std::vector<float>>>> GetStdDev() {
    return fStd;
  }
};

class TFArrayReader {
private:
  CalibReadWriter fRW;
  vector4_float fTF;
  std::vector<int32_t> fAdcSteps;


public:
  explicit TFArrayReader(const std::string& filePath) {
    fRW.ReadTfData(filePath, fAdcSteps, fTF);
  }

  std::vector<std::vector<std::vector<std::vector<float>>>> GetTF() {
    return fTF;
  }

  std::vector<int32_t> GetAdcSteps() {
    return fAdcSteps;
  }
};

class TFInputArrayReader {
private:
  CalibReadWriter fRW;
  vector4_float fTFInput;
  vector4_float fHits;
  std::vector<float> fAmplitude;

public:
  explicit TFInputArrayReader(const std::string& filePath) {
    fRW.ReadTfInput(filePath, fAmplitude, fTFInput, fHits);
  }

  std::vector<std::vector<std::vector<std::vector<float>>>> GetTFInput() {
    return fTFInput;
  }

  std::vector<std::vector<std::vector<std::vector<float>>>> GetHits() {
    return fHits;
  }

  std::vector<float> GetAmplitude() {
    return fAmplitude;
  }

  void FreeMemory() {
    fTFInput.clear();
    fHits.clear();
    fAmplitude.clear();
  }
};

class CFArrayReader {
private:
  CalibReadWriter fRW;
  vector2_float fCF;

public:
  explicit CFArrayReader(const std::string& filePath) {
    fRW.ReadCfData(filePath, fCF);
  }

  std::vector<std::vector<float>> GetCF() {
    return fCF;
  }
};


}}


#endif //INCLUDE_TARGETCALIB_CALIBARRAYREADER_H_

#pragma clang diagnostic pop
