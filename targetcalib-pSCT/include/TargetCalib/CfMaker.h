// Copyright (c) 2016 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains the generic interface for all target modules
 */
#ifndef INCLUDE_TARGETCALIB_CFMAKER_H_
#define INCLUDE_TARGETCALIB_CFMAKER_H_

#include <unistd.h>
#include <iostream>
#include <string>
#include <vector>
#include <iomanip>
#include <map>

#include "TargetCalib/CalibReadWriter.h"
#include "TargetCalib/Constants.h"
#include "TargetCalib/Logger.h"

// For bounds checking only - vectors are used to store look-up values
//#define N_TMPIX 64

namespace CTA {
namespace TargetCalib {

/*!
* @class CfMaker
* @brief Generate pedestal data from TARGET Module data
*/
class CfMaker {

 public:

  /*! Default constructor*/
  CfMaker(const uint16_t nTm=32);

  /*! Empty the vectors*/
  void Clear();
  
  /*! Set a single factor */
  bool Set(const uint16_t tm, const uint16_t tmpix, float cf);

  /*! Set all the factors
   * Assumes all pixels are in the order read from TargetIO */
  bool SetAll(const float* cf, const size_t cfSize);

  /*! Set all the factors*/
  bool SetAll(const uint16_t* tm, const size_t tmSize,
              const uint16_t* tmpix, const size_t tmpixSize,
              const float* cf, const size_t cfSize);
  
  /*! Save the contents of fTm and fPed to file*/
  bool Save(const std::string fileName, const bool compress);

  /*! Accessor: Cf */
  std::vector<std::vector<float>> GetCf() {
    return fCf;
  }

 private:

  uint16_t fNtm;
  std::vector<std::vector<float>> fCf;
  
  /* Check that the tm are pix are ok */
  bool CheckBounds(uint16_t tm, uint16_t tmpix=0);
};

}  // namespace TargetCalib
}  // namespace CTA
#endif  // INCLUDE_TARGETCALIB_CFMAKER_H_
