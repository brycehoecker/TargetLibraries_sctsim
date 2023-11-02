// Copyright (c) 2016 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains the generic interface for all target modules
 */
#pragma clang diagnostic push
#pragma ide diagnostic ignored "OCUnusedGlobalDeclarationInspection"
#ifndef INCLUDE_TARGETCALIB_CALIBRATOR_H_
#define INCLUDE_TARGETCALIB_CALIBRATOR_H_

#include <cstdio>
#include <climits>
#include <cmath>
#include <unistd.h>
#include <vector>
#include <memory>

#include "TargetCalib/CalibReadWriter.h"
#include "TargetCalib/Constants.h"
#include "TargetCalib/Logger.h"
#include "TargetCalib/Utils.h"

namespace CTA {
namespace TargetCalib {

class Calibrator;

struct Ped {
  uint16_t nTM = 0;
  uint16_t nTMPix = 0;
  uint16_t nBlocks = 0;
  uint16_t nSamplesBP = 0;
  bool loadedLookup = false;
  float* lookup = nullptr;
  float* lookupCurrent = nullptr;

  ~Ped() {
    lookupCurrent = nullptr;
    delete[] lookup;
    lookup = nullptr;
  }
};

struct TFCF {
  uint16_t nTM = 0;
  uint16_t nTMPix = 0;
  uint16_t nCells = 0;
  uint16_t nPnts = 0;
  uint16_t adcStep = 0;
  int32_t adcMin = 0;
  int32_t adcMax = 0;
  std::vector<int32_t> adcStepsV;
  std::vector<float> adcStepsSepInvV;
  std::vector<uint32_t> adcStepIndex;
  bool loadedLookup = false;
  float* lookup = nullptr;
  float* lookupCurrent = nullptr;
  uint16_t (Calibrator::*GetCell)(uint16_t) = nullptr;

  ~TFCF() {
    lookupCurrent = nullptr;
    delete[] lookup;
    lookup = nullptr;
  }
};

/*!
* @class Calibrator
* @brief Apply calibration
*/
class Calibrator {
private:

  uint16_t fCurrentBlockphase;
  uint16_t fCurrentBlock;
  uint16_t fCurrentFirstCellID;

  bool fLoadPrintTitle = false;

  float TfCfScale(float val, uint16_t sample);
  uint16_t GetSamplingCell(uint16_t sample);
  uint16_t GetStorageCell(uint16_t sample);

  /*! Load Pedestals */
  bool LoadPed(std::string fileName, vector4_float& pedestal);

  /*! Populate Integer Pedestals look-up */
  bool MakePedLookup(vector4_float& pedestal);

  bool MakeLookupFullCamera(vector4_float& tf, vector3_float& cf);
  bool MakeLookupSingleTF(vector4_float& tf, vector3_float& cf);

  /*! Populate multiplicative look-up*/
  bool MakeLookup(vector4_float& tf, vector3_float& cf);

//  bool CheckBounds(uint16_t tm, uint16_t tmpix=0, uint16_t cell=0);

protected:

  uint16_t fNtm;
  bool fPotentialOverflow = false;

  std::shared_ptr<Ped> fPed;
  std::shared_ptr<TFCF> fTfCf;

  /*! Load a TF */
  bool LoadTf(std::string fileName, vector4_float& tf);

  /*! Load a CF */
  bool LoadCf(std::string fileName, vector3_float& cf);


public:

  /*! Default constructor */
  explicit Calibrator(std::string pedFileName,
                      std::string tfFileName = "",
                      std::vector<std::string> cfFileNames={});

  explicit Calibrator(const std::string& pedPath, const int16_t SN) :
    Calibrator(pedPath, GetTFPath(SN)) {}

  /*! Apply to an entire event
   *  Assumes pixels are ordered in the same order they are read from TargetIO
   *  Size of each array needed for python interface
   *  To be used from python via SWIG */
  void ApplyEvent(const uint16_t* wfs, size_t nPix, size_t nSamples,
                  const uint16_t* fci, size_t fciNPix,
                  float* wfsC, size_t nPixC, size_t nSamplesC);

  /*! Apply to a waveform 
   *  To be used in C++ executable */
  void ApplyWaveform(
    const uint16_t *wf, float *wfCal, size_t nSamples,
    uint16_t tm, uint16_t tmpix,
    uint16_t row, uint16_t column, uint16_t blockphase
  );

  /*! Set the Cell information for the event, saving the calculations being
   *  done for every sample. Should be called per packet.
   */
  virtual void SetPacketInfo(uint16_t tm,
                             uint16_t row,
                             uint16_t column,
                             uint16_t blockphase);

  /*! Set the starting point for a wf lookup index based on tm and tmpix
   *  to save doing it for every cell
   *  To be used in C++ executable */
  virtual void SetLookupPosition(uint16_t tm, uint16_t tmpix);
    
  /*! Apply to a cell
   *  To be used in C++ executable */
  float ApplySample(float val, uint16_t sample);

  /*! Apply to an array of samples, all from the same tm, pixel & cell
   *  To be used from python via SWIG */
  void ApplyArray(
    const float *wf, size_t nSamples_i,
    float *wfCal, size_t nSamples_o,
    uint16_t tm, uint16_t tmpix,
    uint16_t row, uint16_t column, uint16_t blockphase
  );

    /*! Accessor: Ped */
  std::vector<std::vector<std::vector<std::vector<float>>>> GetPedLookup() {
    vector4_float ped;
    ped.resize(fPed->nTM);
    for (uint32_t tm=0; tm<fPed->nTM; ++tm) {
      ped[tm].resize(fPed->nTMPix);
      for (uint32_t pix=0; pix<fPed->nTMPix; ++pix) {
        ped[tm][pix].resize(fPed->nBlocks);
        for (uint32_t blk=0; blk<fPed->nBlocks; ++blk) {
          ped[tm][pix][blk].resize(fPed->nSamplesBP);
          for (uint32_t sampbp=0; sampbp<fPed->nSamplesBP; ++sampbp) {
            uint32_t i = ((tm*fPed->nTMPix + pix)*fPed->nBlocks + blk)
                         * fPed->nSamplesBP + sampbp;
            ped[tm][pix][blk][sampbp] = fPed->lookup[i];
          }
        }
      }
    }

    return ped;
  }

  /*! Accessor: TF */
  std::vector<std::vector<std::vector<std::vector<float>>>> GetTfCfLookup() {
    vector4_float tfcf;
    tfcf.resize(fTfCf->nTM);
    for (uint32_t tm=0; tm<fTfCf->nTM; ++tm) {
      tfcf[tm].resize(fTfCf->nTMPix);
      for (uint32_t pix=0; pix<fTfCf->nTMPix; ++pix) {
        tfcf[tm][pix].resize(fTfCf->nCells);
        for (uint32_t cell=0; cell<fTfCf->nCells; ++cell) {
          tfcf[tm][pix][cell].resize(fTfCf->nPnts);
          for (uint32_t pnt=0; pnt<fTfCf->nPnts; ++pnt) {
            uint32_t i = ((tm*fTfCf->nTMPix + pix)*fTfCf->nCells + cell)
                         * fTfCf->nPnts + pnt;
            tfcf[tm][pix][cell][pnt] = fTfCf->lookup[i];
          }
        }
      }
    }

    return tfcf;
  }

  /*! Accessor: AdcMin */
  float GetAdcMin(){
    return fTfCf->adcMin;
  }

  /*! Accessor: AdcStep */
  float GetAdcStep() {
    return fTfCf->adcStep;
  }
//
//  /*! Print fPed for a given pixel */
//  bool PrintPed(const uint16_t tm, const uint16_t tmpix);
//
//  /*! Print TF for a given cell */
//  bool PrintTf(const uint16_t tm, const uint16_t tmpix, const uint16_t cell);
 
};

}  // namespace TargetCalib
}  // namespace CTA
#endif  // INCLUDE_TARGETCALIB_CALIBRATOR_H_

#pragma clang diagnostic pop