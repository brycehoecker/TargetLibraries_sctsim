// Copyright (c) 2016 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains the generic interface for all target modules
 */
#ifndef INCLUDE_TARGETCALIB_PEDESTALMAKER_H_
#define INCLUDE_TARGETCALIB_PEDESTALMAKER_H_

#include <unistd.h>
#include <iostream>
#include <string>
#include <vector>
#include <set>
#include <iomanip>
#include <map>
#include <cmath>
#include <iterator>

#include "TargetCalib/CalibReadWriter.h"
#include "TargetCalib/Constants.h"
#include "TargetCalib/Logger.h"
#include "TargetCalib/Utils.h"

namespace CTA {
namespace TargetCalib {

/*!
* @class PedestalMaker
* @brief Generate pedestal data from TARGET Module data
*/
class PedestalMaker {
private:

  uint16_t fNtm;
  uint16_t fNBlocks;
  uint16_t fNSamples;
  uint16_t fNSamplesBP;
  bool fDiagnostic;
  float fMinHits;
  float fMaxHits;
  std::set<uint16_t> fBlockphases;
  uint16_t fMinSamplesBP;
  uint16_t fMaxSamplesBP;
  vector4_float fPed;
  vector4_float fHits;
  vector4_float fPed2;
  vector4_float fStd;

public:

  /*! Default constructor*/
  explicit PedestalMaker(uint16_t nTm=32, uint16_t nBlocks=512,
                         uint16_t nSamples=96, bool diagnostic=false);

  /*! Empty the vectors*/
  void Clear();

  /*! Add entire event's waveforms to the pedestal vector
   * Assumes pixels are ordered in the same order they are read from TargetIO
   * To be used from python via SWIG */
  bool AddEvent(const uint16_t* wfs, size_t nPix, size_t nSamples,
                const uint16_t* fci, size_t fciNPix);

  /*! Add waveform to the pedestal vector
   *  To be used in C++ executable */
  bool AddWaveform(const uint16_t* wf, size_t nSamples,
                   uint16_t tm, uint16_t tmpix,
                   uint16_t blk, uint16_t blkPhase);

  /*! Add waveform to the pedestal vector
   *  To be used in C++ executable */
  bool AddSample(uint16_t adc, uint16_t sample,
                 uint16_t tm, uint16_t tmpix,
                 uint16_t blk, uint16_t blkPhase);

  /*! Save the contents of fTm and fPed to file */
  bool Save(const std::string& fileName, bool compress);

  /*! Check to see if the number of hits in each cell exceeds a threshold */
  bool CheckHits(uint16_t thresh);

  /*! Accessor: Ped */
  std::vector<std::vector<std::vector<std::vector<float>>>> GetPed() {
    return fPed;
  }

  /*! Accessor: Hits */
  std::vector<std::vector<std::vector<std::vector<float>>>> GetHits() {
    return fHits;
  }

  /*! Accessor: Min Max Hits */
  void GetMinMaxHits(float &min, float &max) {
    min = fMinHits;
    max = fMaxHits;
  }

  /*! Accessor: Standard Deviation */
  std::vector<std::vector<std::vector<std::vector<float>>>> GetStd() {
    return fStd;
  }

};

}  // namespace TargetCalib
}  // namespace CTA
#endif  // INCLUDE_TARGETCALIB_PEDESTALMAKER_H_
