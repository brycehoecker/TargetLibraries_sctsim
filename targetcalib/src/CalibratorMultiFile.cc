// Copyright (c) 2016 The CTA Consortium. All rights reserved.
#include "TargetCalib/CalibratorMultiFile.h"

namespace CTA {
namespace TargetCalib {

void CalibratorMultiFile::Init(
  const std::vector<std::string> tfFileNames,
  const std::vector<std::string> cfFileNames
) {
  fTfCfVector.assign(fNtm, nullptr);
  vector3_float cf;

  for (size_t cfFile=0; cfFile<cfFileNames.size(); ++cfFile) { // NOLINT
    if (!cfFileNames[cfFile].empty()) {
      if (!LoadCf(cfFileNames[cfFile], cf)) {
        GERROR << "Could not load cf file " << cfFileNames[cfFile];
      }
    }
  }

  bool onetf = false;
  for (size_t tm=0; tm<fNtm; ++tm) {
    if (!tfFileNames[tm].empty()) {
      fTfCfVector[tm] = std::make_shared<TFCF>();
      fTfCf = fTfCfVector[tm];
      vector4_float tf_module;
      if (!LoadTf(tfFileNames[tm], tf_module)) {
        GERROR << "Could not load TF file " << tfFileNames[tm];
      }
      if(!MakeLookupMultiTF(tf_module, cf, tm)) {
        GERROR << "Could not construct lookup table";
      }
      onetf = true;
    }
  }

  if (!onetf) {
    GERROR << "No TF files are found, "
              "have you correctly setup CHECDevelopment and TC_CONFIG_PATH?";
  }
}

bool CalibratorMultiFile::MakeLookupMultiTF(vector4_float& tf,
                                            vector3_float& cf, size_t tm){

  bool loadedTF = !tf.empty();

  fTfCf->loadedLookup = false;
  fTfCf->lookup = new float[N_TMPIX * fTfCf->nCells * fTfCf->nPnts];
  for (size_t tmpix=0; tmpix<N_TMPIX; ++tmpix){
    for (size_t cell=0; cell<fTfCf->nCells; ++cell) {
      for (size_t pnt=0; pnt<fTfCf->nPnts; ++pnt) {
        size_t i = (tmpix * fTfCf->nCells + cell) * fTfCf->nPnts + pnt;
        fTfCf->lookup[i] = 1.0;
        if (loadedTF) fTfCf->lookup[i] *= tf[0][tmpix][cell][pnt];
        for (auto &cfFile : cf) {
          if (!cfFile.empty())
            fTfCf->lookup[i] *= cfFile[tm][tmpix];
        }
      }
    }
  }
  fTfCf->loadedLookup = true;
  return true;
}


void CalibratorMultiFile::SetPacketInfo(uint16_t tm,
                                        uint16_t row,
                                        uint16_t column,
                                        uint16_t blockphase) {
  fTfCf = fTfCfVector[tm];
  Calibrator::SetPacketInfo(tm, row, column, blockphase);
}

void CalibratorMultiFile::SetLookupPosition(const uint16_t tm,
                                            const uint16_t tmpix) {
  auto pix = (uint32_t) tm * N_TMPIX + tmpix;
  auto pedPos = (uint32_t) (pix * fPed->nBlocks * fPed->nSamplesBP);
  auto tmPos = (uint32_t) (tmpix * fTfCf->nCells * fTfCf->nPnts);
  fPed->lookupCurrent = fPed->lookup + pedPos;
  fTfCf->lookupCurrent = fTfCf->lookup + tmPos;
  fPotentialOverflow = false;
}

}
}
