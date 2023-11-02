// Copyright (c) 2016 The CTA Consortium. All rights reserved.

#include "TargetCalib/Calibrator.h"

namespace CTA {
namespace TargetCalib {
 
Calibrator::Calibrator(const std::string pedFileName,
                       const std::string tfFileName,
                       const std::vector<std::string> cfFileNames) :
  fNtm(0),
  fPed(std::make_shared<Ped>()),
  fTfCf(std::make_shared<TFCF>())
{
  vector4_float pedestal;
  vector4_float tf;
  vector3_float cf;


  if(!pedFileName.empty()) {
    if(!LoadPed(pedFileName, pedestal)){
      GERROR << "Could not load pedestal file " << pedFileName;
    }
    if(!MakePedLookup(pedestal)) {
      GERROR << "Could not construct pedestal lookup table";
    }
  }
  else {
    GWARNING << "Pedestal file not specified.. this is usually bad!";
  }

  if(!tfFileName.empty()) {
    if(!LoadTf(tfFileName, tf)){
      GERROR << "Could not load TF file " << tfFileName;
    }
  }
  bool tfLoaded = !tf.empty();

  bool cfLoaded = false;
  for (size_t cfFile=0; cfFile<cfFileNames.size(); ++cfFile) { // NOLINT
    if (!cfFileNames[cfFile].empty()) {
      if (!LoadCf(cfFileNames[cfFile], cf)) {
        GERROR << "Could not load cf file " << cfFileNames[cfFile];
      }
      if (!cf[cfFile].empty()) cfLoaded = true;
    }
  }

  if (tfLoaded || cfLoaded) {
    if(!MakeLookup(tf, cf)) {
      GERROR << "Could not construct lookup table";
    }
  }
}

bool Calibrator::LoadPed(const std::string fileName, vector4_float& pedestal){

  GDEBUG << "Loading pedestal file: " << fileName;

  auto* cr = new CalibReadWriter();
  if(cr->ReadPedestalData(fileName, pedestal)!=TCAL_FILE_OK) {
    GERROR << "Could not load pedestal file:" << fileName;
    return false;
  }

  if (pedestal.empty()) {
    GERROR << "Pedestal vector is empty";
    return false;
  }

  fPed->nTM = (uint16_t) pedestal.size();
  fPed->nTMPix = (uint16_t) pedestal[0].size();
  fPed->nBlocks = (uint16_t) pedestal[0][0].size();
  fPed->nSamplesBP = (uint16_t) pedestal[0][0][0].size();

  GDEBUG << "Number of TM in Ped File: " << fPed->nTM;
  GDEBUG << "Number of TMPIX in Ped File: " << fPed->nTMPix;
  GDEBUG << "Number of BLOCKS in Ped File: " << fPed->nBlocks;
  GDEBUG << "Number of SAMPLEBP in Ped File: " << fPed->nSamplesBP;

  // Do not allow calibration from calib files with different numbers of TM
  if (fNtm==0) fNtm = fPed->nTM;
  else if (fPed->nTM != fNtm)
    GERROR << "Mismatch between number of TMs specified ("
           << fNtm << ") and that in pedestal file (" << fPed->nTM << ")";

  if (fPed->nTM > N_TM_MAX)
    GERROR << "Pedestal file contains too many TMs: " << fPed->nTM;

  if (fPed->nTMPix != N_TMPIX)
    GERROR << "Pedestal file contains invalid number of tmpix: " << fPed->nTMPix;

  delete cr;
  return true;
}

bool Calibrator::LoadTf(const std::string fileName, vector4_float& tf){

  auto* cr = new CalibReadWriter();
  if (cr->ReadTfData(fileName, fTfCf->adcStepsV, tf)!=TCAL_FILE_OK) {
    GERROR << "Could not load transfer function file:" << fileName;
    return false;
  }

  if (tf.empty()) {
    GERROR << "TF vector is empty";
    return false;
  }

  fTfCf->nTM = (uint16_t) tf.size();
  fTfCf->nTMPix = (uint16_t) tf[0].size();
  fTfCf->nCells = (uint16_t) tf[0][0].size();
  fTfCf->nPnts = (uint16_t) tf[0][0][0].size();

  for (uint32_t i=0; i<fTfCf->adcStepsV.size()-1; ++i) {
    int32_t step = fTfCf->adcStepsV[i];
    int32_t nextStep = fTfCf->adcStepsV[i+1];
    fTfCf->adcStepsSepInvV.push_back((float) 1./(nextStep - step));
    for (int32_t j=step; j<nextStep; ++j) {
      fTfCf->adcStepIndex.push_back(i);
    }
  }
  fTfCf->adcMin = fTfCf->adcStepsV.front();
  fTfCf->adcMax = fTfCf->adcStepsV.back();

  if (fNtm==0) fNtm = fTfCf->nTM;
  else if (fTfCf->nTM != fNtm && fTfCf->nTM != 1)
    GERROR << "Mismatch between number of TMs in calibration files";

  if (fTfCf->nTM > N_TM_MAX)
    GERROR << " TF file contains too many TMs: " << fTfCf->nTM;

  if (fTfCf->nTMPix != N_TMPIX)
    GERROR << " TF file contains invalid number of tmpix: " << fTfCf->nTMPix;

  if (fTfCf->nCells == N_SAMPLINGCELL) {
    fTfCf->GetCell = &Calibrator::GetSamplingCell;
  } else if (fTfCf->nCells == N_STORAGECELL) {
    fTfCf->GetCell = &Calibrator::GetStorageCell;
  } else {
    GERROR << " TF file contains invalid number of cells: " << fTfCf->nCells;
  }

  if (fTfCf->nPnts <= 1)
    GERROR << " TF file contains invalid number of points: " << fTfCf->nPnts;

  if (!fLoadPrintTitle) {
    GDEBUG <<'|'<<std::left<< std::setw(23) << std::setfill(' ') << "FilePath"
           <<'|'<<std::left<< std::setw(3) << std::setfill(' ') << "nTM"
           <<'|'<<std::left<< std::setw(5) << std::setfill(' ') << "nCell"
           <<'|'<<std::left<< std::setw(8) << std::setfill(' ') << "fAdcStep"
           <<'|'<<std::left<< std::setw(7) << std::setfill(' ') << "fAdcMin"
           <<'|'<<std::left<< std::setw(7) << std::setfill(' ') << "fAdcMax"
           <<'|'<<std::left<< std::setw(6) << std::setfill(' ') << "fNpnts";
    fLoadPrintTitle = true;
  }

  std::string pFileName = fileName;
  if (fileName.size() > 20) {
    pFileName = "..." + fileName.substr(fileName.size() - 20);
  }
  GDEBUG <<'|'<<std::left<< std::setw(23) << std::setfill(' ') << pFileName
         <<'|'<<std::left<< std::setw(3 ) << std::setfill(' ') << fTfCf->nTM
         <<'|'<<std::left<< std::setw(5 ) << std::setfill(' ') << fTfCf->nCells
         <<'|'<<std::left<< std::setw(8 ) << std::setfill(' ') << fTfCf->adcStep
         <<'|'<<std::left<< std::setw(7 ) << std::setfill(' ') << fTfCf->adcMin
         <<'|'<<std::left<< std::setw(7 ) << std::setfill(' ') << fTfCf->adcMax
         <<'|'<<std::left<< std::setw(6 ) << std::setfill(' ') << fTfCf->nPnts;

  delete cr;
  return true;
}

bool Calibrator::LoadCf(const std::string fileName, vector3_float& cf){

  GDEBUG << "Loading file: " <<fileName;

  auto * cr = new CalibReadWriter();
  vector2_float cfi;
  if(cr->ReadCfData(fileName, cfi)!=TCAL_FILE_OK) {
    GERROR << "Could not load file:" << fileName;
    return false;
  }

  if (cfi.empty()) {
    GERROR << "Vector is empty";
    return false;
  }

  if (fNtm==0) fNtm = (uint16_t)cfi.size();
  else if ((uint16_t) cfi.size() != fNtm)
    GERROR << "Mismatch between number of TMs in calibration files";

  if ((uint16_t) cfi.size() > N_TM_MAX)
    GERROR << "File contains too many TMs: " << cfi.size();

  if ((uint16_t) cfi[0].size() != N_TMPIX)
    GERROR << "File contains invalid number of tmpix: " << cfi[0].size();

  cf.push_back(cfi);

  delete cr;
  return true;
}

bool Calibrator::MakePedLookup(vector4_float& pedestal){

  fPed->loadedLookup = false;

  if(pedestal.empty()) {
    GWARNING << "Pedestal vector is empty";
    return false;
  }

  fPed->lookup = new float[fNtm * N_TMPIX * fPed->nBlocks * fPed->nSamplesBP];
  for (size_t tm=0; tm<fPed->nTM; ++tm){
    for (size_t tmpix=0; tmpix<fPed->nTMPix; ++tmpix){
      for (size_t blk=0; blk<fPed->nBlocks; ++blk) {
        for (size_t sampBP=0; sampBP<fPed->nSamplesBP; ++sampBP) {
          size_t pix = tm * N_TMPIX + tmpix;
          size_t i = (pix * fPed->nBlocks + blk) * fPed->nSamplesBP + sampBP;
          fPed->lookup[i] = pedestal[tm][tmpix][blk][sampBP];
        }
      }
    }
  }
  fPed->loadedLookup = true;
  return true;
}

bool Calibrator::MakeLookupFullCamera(vector4_float& tf, vector3_float& cf){

  bool loadedTF = !tf.empty();

  fTfCf->loadedLookup = false;

  fTfCf->lookup = new float[fNtm * N_TMPIX * fTfCf->nCells * fTfCf->nPnts];

  for (size_t tm=0; tm<fNtm; ++tm){
    for (size_t tmpix=0; tmpix<N_TMPIX; ++tmpix){
      for (size_t cell=0; cell<fTfCf->nCells; ++cell) {
        for (size_t pnt=0; pnt<fTfCf->nPnts; ++pnt) {
          size_t pix = tm * N_TMPIX + tmpix;
          size_t i = (pix * fTfCf->nCells + cell) * fTfCf->nPnts + pnt;
          fTfCf->lookup[i] = 1.0;
          if (loadedTF) fTfCf->lookup[i] *= tf[tm][tmpix][cell][pnt];
          for (auto &cfFile : cf) {
            if (!cfFile.empty())
              fTfCf->lookup[i] *= cfFile[tm][tmpix];
          }
        }
      }
    }
  }
  fTfCf->loadedLookup = true;
  return true;
}

bool Calibrator::MakeLookupSingleTF(vector4_float& tf, vector3_float& cf){

  bool loadedTF = !tf.empty();

  fTfCf->loadedLookup = false;

  fTfCf->lookup = new float[fNtm * N_TMPIX * fTfCf->nCells * fTfCf->nPnts];

  for (size_t tm=0; tm<fNtm; ++tm){
    for (size_t tmpix=0; tmpix<N_TMPIX; ++tmpix){
      for (size_t cell=0; cell<fTfCf->nCells; ++cell) {
        for (size_t pnt=0; pnt<fTfCf->nPnts; ++pnt) {
          size_t pix = tm * N_TMPIX + tmpix;
          size_t i = (pix * fTfCf->nCells + cell) * fTfCf->nPnts + pnt;
          fTfCf->lookup[i] = 1.0;
          if (loadedTF) fTfCf->lookup[i] *= tf[0][tmpix][cell][pnt];
          for (auto &cfFile : cf) {
            if (!cfFile.empty())
              fTfCf->lookup[i] *= cfFile[tm][tmpix];
          }
        }
      }
    }
  }
  fTfCf->loadedLookup = true;
  return true;
}

bool Calibrator::MakeLookup(vector4_float& tf, vector3_float& cf){
  if (fTfCf->nTM == 1) return MakeLookupSingleTF(tf, cf);
  else return MakeLookupFullCamera(tf, cf);
}

#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wunused-parameter"
#pragma ide diagnostic ignored "OCUnusedGlobalDeclarationInspection"
void Calibrator::ApplyEvent(
  const uint16_t* wfs, const size_t nPix, const size_t nSamples,
  const uint16_t* fci, const size_t fciNPix,
  float* wfsC, const size_t nPixC, const size_t nSamplesC
) {
  uint16_t row;
  uint16_t column;
  uint16_t blockPhase;
  for (size_t i=0; i<nPix; ++i) {
    CalculateRowColumnBlockPhase(fci[i], row, column, blockPhase);
    auto* wf = (uint16_t*) (wfs + i*nSamples);
    float* wfC = wfsC + i * nSamples;
    auto tm = (uint16_t) (i / N_TMPIX);
    auto tmpix = (uint16_t) (i % N_TMPIX);
    ApplyWaveform(wf, wfC, nSamples, tm, tmpix, row, column, blockPhase);
  }
}
#pragma clang diagnostic pop

void Calibrator::ApplyWaveform(
  const uint16_t *wf, float *wfCal, const size_t nSamples,
  const uint16_t tm, const uint16_t tmpix,
  const uint16_t row, const uint16_t column, const uint16_t blockphase
){
  SetPacketInfo(tm, row, column, blockphase);
  SetLookupPosition(tm, tmpix);
  for (uint16_t isam=0; isam<nSamples; ++isam) {
    wfCal[isam] = ApplySample((float) wf[isam], isam);
  }
}

#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wunused-parameter"
void Calibrator::SetPacketInfo(uint16_t tm,
                               uint16_t row,
                               uint16_t column,
                               uint16_t blockphase) {
  fCurrentBlockphase = blockphase;
  fCurrentBlock = (uint16_t) (column * 8 + row);
  fCurrentFirstCellID = (uint16_t) (fCurrentBlock * N_BLOCKPHASE + blockphase);
}
#pragma clang diagnostic pop

void Calibrator::SetLookupPosition(const uint16_t tm, const uint16_t tmpix) {
  auto pix = (uint32_t) tm * N_TMPIX + tmpix;
  auto pedPos = (uint32_t) (pix * fPed->nBlocks * fPed->nSamplesBP);
  auto tmPos = (uint32_t) (pix * fTfCf->nCells * fTfCf->nPnts);
  fPed->lookupCurrent = fPed->lookup + pedPos;
  fTfCf->lookupCurrent = fTfCf->lookup + tmPos;
  fPotentialOverflow = false;
}

float Calibrator::ApplySample(const float val, const uint16_t sample){

  float cal = val;

  if (fPed->loadedLookup) {
    uint16_t sampleBP = fCurrentBlockphase + sample;
    float ped = fPed->lookupCurrent[fCurrentBlock * fPed->nSamplesBP +sampleBP];
    if (cal == 0. && !fPotentialOverflow) return 0; // Handle disconnected pixels
    else if (ped == 0.) return 0; // Set samples to zero if pedestal absent
    else cal -= ped;

#ifdef CHECS
    // Overflow handling
    if (cal > 1200) fPotentialOverflow = true;
    else if (fPotentialOverflow && cal < -100) cal += 4096;
    else if (fPotentialOverflow && cal < 1200) fPotentialOverflow = false;
#elif defined(CHECM)
    if (val < 10 && val > 1) cal = fTfCf->adcMax; // Saturated (TARGET-5)
#elif SCT
#else
#error No camera keyword defined
#endif
  }
  if (fTfCf->loadedLookup) cal = TfCfScale(cal, sample);
  return cal;

}

#pragma clang diagnostic push
#pragma ide diagnostic ignored "OCUnusedGlobalDeclarationInspection"
#pragma clang diagnostic ignored "-Wunused-parameter"
void Calibrator::ApplyArray(
  const float *wf, const size_t nSamples_i,
  float *wfCal, const size_t nSamples_o,
  const uint16_t tm, const uint16_t tmpix,
  const uint16_t row, const uint16_t column, const uint16_t blockphase
){
  SetPacketInfo(tm, row, column, blockphase);
  SetLookupPosition(tm, tmpix);
  for (uint32_t isam=0; isam<nSamples_i; ++isam) {
    float val = wf[isam];
    wfCal[isam] = ApplySample(val, 0);
  }
}
#pragma clang diagnostic pop

float Calibrator::TfCfScale(const float val, const uint16_t sample) {
  uint16_t cell = (this->*fTfCf->GetCell)(sample);
  float* lookup = fTfCf->lookupCurrent;
  if (lround(val) <= fTfCf->adcMin) {
    uint32_t index = cell * fTfCf->nPnts;
    return lookup[index];
  } else if (lround(val) >= fTfCf->adcMax) {
    uint32_t index = (uint32_t) ((cell + 1) * fTfCf->nPnts) - 1;
    return lookup[index];
  } else {
    uint32_t pnt = fTfCf->adcStepIndex[val - fTfCf->adcMin];
    uint32_t index = cell * fTfCf->nPnts + pnt;
    return lookup[index] + (val - fTfCf->adcStepsV[pnt]) *
                             (lookup[index+1]-lookup[index]) *
                             fTfCf->adcStepsSepInvV[pnt];
  }
}

uint16_t Calibrator::GetSamplingCell(const uint16_t sample) {
  auto cell = (uint16_t) ((fCurrentFirstCellID + sample) % N_SAMPLINGCELL);
  return cell;
}

uint16_t Calibrator::GetStorageCell(const uint16_t sample) {
  auto factor = (uint16_t) (64 * (1 - 2 * (fCurrentBlock % 2)));
  auto shift = (uint16_t) ((((fCurrentBlockphase + sample) / 32) % 2) * factor);
  auto cell = (uint16_t) ((fCurrentFirstCellID + sample + shift)%N_STORAGECELL);
  return cell;
}


//bool Calibrator::CheckBounds(uint16_t tm, uint16_t tmpix, uint16_t cell) {
//
//  bool ok = true;
//  if(tm>=fNtm) {
//    GERROR << "Invalid tm" << tm << " (" << fNtm << ")";
//    ok = false;
//  }
//
//  if(tmpix>=N_TMPIX) {
//    GERROR << "Invalid pixel " << tmpix << " (" << N_TMPIX << ")";
//    ok = false;
//  }
//
//  if (cell>N_CELL_PED) {
//    GERROR << "Invalid cell " << cell << " (" << N_CELL_PED << ")";
//    ok = false;
//  }
//
//  return ok;
//}

//  // Need to update for blocks
//bool Calibrator::PrintPed(const uint16_t tm, const uint16_t tmpix) {
//
//  if(!CheckBounds(tm,tmpix)) return false;
//
//  std::cout << "TM=" << tm << ", PIX=" << tmpix << std::endl;
//  for (uint16_t cell=0; cell<N_CELL_PED; cell+=32) {
//    for (int i=0; i<32; i++) {
//      std::cout << std::setw(8) << std::setprecision(6) << fPed[tm][tmpix][cell+i][0];
//    }
//    std::cout << std::endl;
//  }
//
//  return true;
//}
//
//bool Calibrator::PrintTf(const uint16_t tm, const uint16_t tmpix,
//                         const uint16_t cell) {
//
//  if(!CheckBounds(tm,tmpix,cell)) return false;
//
//  std::cout << "TM=" << tm << ", PIX=" << tmpix
//            << ", CELL=" << cell<< std::endl;
//
//  for (uint16_t pnt=0; pnt<fNpnts; pnt++){
//    std::cout << "ADC=" << fAdcMin + pnt*fAdcStep
//              << ", V=" << fTf[tm][tmpix][cell][pnt] << std::endl;
//  }
//
//  return true;
//}
 
}
}
