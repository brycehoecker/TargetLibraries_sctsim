// Copyright (c) 2016 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains the generic interface for all target modules
 */
#ifndef INCLUDE_TARGETCALIB_CALIBRATORMULTIFILE_H_
#define INCLUDE_TARGETCALIB_CALIBRATORMULTIFILE_H_

#include "TargetCalib/Calibrator.h"

namespace CTA {
namespace TargetCalib {

/*!
* @class Calibrator
* @brief Apply calibration
*/
class CalibratorMultiFile: public Calibrator {
private:

  std::vector<std::shared_ptr<TFCF>> fTfCfVector;

public:

  /*! Default constructor */
  CalibratorMultiFile(std::string& pedFileName,
                      std::vector<std::string> tfFileNames,
                      std::vector<std::string> cfFileNames={})
                      : Calibrator(pedFileName) {
    Init(tfFileNames, cfFileNames);
  }

  CalibratorMultiFile(const std::string& pedFileName,
                      const std::vector<int16_t>& SNs)
                      : Calibrator(pedFileName) {
    std::vector<std::string> tfPaths(SNs.size(), "");
    std::cout << "[CalibratorConstructor] TF file for each module:" << std::endl;
    for (size_t tm = 0; tm < SNs.size(); ++tm) {
      int16_t sn = SNs[tm];
      tfPaths[tm] = GetTFPath(sn);
      std::cout << "\tTM: " << tm << " SN: " << sn << " PATH: " << tfPaths[tm]
                << std::endl;
    }
    Init(tfPaths);
  }

  void Init(std::vector<std::string> tfFileNames,
            std::vector<std::string> cfFileNames={});

  /*! Populate multiplicative look-up*/
  bool MakeLookupMultiTF(vector4_float& tf, vector3_float& cf, size_t tm);

  void SetPacketInfo(uint16_t tm,
                     uint16_t row,
                     uint16_t column,
                     uint16_t blockphase) override;

  /*! Set the starting point for a wf lookup index based on tm and tmpix
   *  to save doing it for every cell
   *  To be used in C++ executable */
  void SetLookupPosition(uint16_t tm, uint16_t tmpix) override;

};

}  // namespace TargetCalib
}  // namespace CTA
#endif  // INCLUDE_TARGETCALIB_CALIBRATORMULTIFILE_H_
