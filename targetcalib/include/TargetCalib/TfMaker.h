// Copyright (c) 2016 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains the generic interface for all target modules
 */
#pragma clang diagnostic push
#pragma ide diagnostic ignored "OCUnusedGlobalDeclarationInspection"
#ifndef INCLUDE_TARGETCALIB_TFMAKER_H_
#define INCLUDE_TARGETCALIB_TFMAKER_H_

//#include <algorithm>
#include <unistd.h>
#include <iostream>
#include <string>
#include <vector>
#include <iomanip>
#include <map>
#include <cmath>
#include <cfloat>

#include "TargetCalib/CalibReadWriter.h"
#include "TargetCalib/Constants.h"
#include "TargetCalib/Logger.h"
#include "TargetCalib/Utils.h"

namespace CTA {
namespace TargetCalib {

/*!
* @class Tf_Maker
* @brief Generate transfer function data from TARGET Module data
*/
class TfMaker {
private:

  size_t fNtm;
  size_t fNCells;

  uint16_t fAmpIndex;

  std::vector<float> fAmplitudeV;
  vector4_float fTfInput;
  vector4_float fHits;
  uint16_t (TfMaker::*GetCell)(uint16_t, uint16_t) = nullptr;

  bool fSkipOverflow = false;

  /* Calulate the interpolated input amplitude for an ADC value */
//  float GetAmplitude(uint16_t tm, uint16_t tmpix, uint16_t cell, int32_t adc);

  void PrepareCellTFInput(
    float& adcMin, float& adcMax, bool& broken,
    std::vector<float>& ampV, std::vector<float>& tfInput
  );

  /* Calulate the interpolated input amplitude for an ADC value */
  float GetAmplitude(
    float adcMin, float adcMax,
    const std::vector<float>& ampV, const std::vector<float>& tfInput,
    int32_t adc
  );

  uint16_t GetSamplingCell(uint16_t fci, uint16_t sample);
  uint16_t GetStorageCell(uint16_t fci, uint16_t sample);

public:

  /*! Default constructor */
  explicit TfMaker(const std::vector<float>& amplitudeV,
                   size_t nTm=32, size_t nCells=64);

  /*! Constructor from existing TFInput */
  explicit TfMaker(std::string fileName);

  /*! Constructor from existing TFInput */
  TfMaker(std::vector<float> amplitude,
          std::vector<std::vector<std::vector<std::vector<float>>>> tfinput,
          std::vector<std::vector<std::vector<std::vector<float>>>> hits);

  /*! Empty the vectors */
  void Clear();

  /*! Set the index in the TF lookup table for a given Amplitude
  - should be called when you change amplitude and are using Add */
  bool SetAmplitudeIndex(float amplitude);

  static std::vector<int32_t> CreateADCStepVector(
    int32_t& adcMin, int32_t& adcMax,
    int32_t& adcMinSecondary, int32_t& adcMaxSecondary,
    uint16_t stepSize, uint16_t stepSizeSecondary
  );

  /*! Add an entire event
   * Assumes pixels are ordered in the same order they are read from TargetIO
   * To be used from python via SWIG */
  bool AddEvent(const float* wfs, size_t nPix, size_t nSamples,
                const uint16_t* fci, size_t fciNPix);

  /*! Add waveform to the fTfInput vector */
  bool AddWaveform(const float* wf, size_t nSamples,
                   uint16_t tm, uint16_t tmpix,
                   uint16_t fci);

  /*! Add single value to the fTfInput vector
   *  To be used in C++ executable */
  bool AddSample(float adc, uint16_t sample,
                 uint16_t tm, uint16_t tmpix,
                 uint16_t fci);

  /*! Save the TfInput to a file */
  bool SaveTfInput(std::string fileName);
  
  /*! Flip axis and save the tf lookup to a file */
  bool Save(std::string fileName, uint16_t adcStep, uint16_t adcStepSecondary,
            uint16_t amplitudeZero, bool compress);
  
  /*! Check to see if the number of hits in each cell exceeds a threshold */
  bool CheckHits(uint16_t thresh);

  /*! Accessors */
  std::vector<std::vector<std::vector<std::vector<float>>>> GetTfInput() {
    return fTfInput;
  }
  std::vector<std::vector<std::vector<std::vector<float>>>> GetHits() {
    return fHits;
  }
  std::vector<float> GetAmplitudeVector() {
    return fAmplitudeV;
  }
};

}  // namespace TargetCalib
}  // namespace CTA
#endif  // INCLUDE_TARGETCALIB_TFMAKER_H_

#pragma clang diagnostic pop