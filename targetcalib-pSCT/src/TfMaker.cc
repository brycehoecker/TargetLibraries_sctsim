// Copyright (c) 2016 The CTA Consortium. All rights reserved.
#include "TargetCalib/TfMaker.h"

#pragma clang diagnostic push
#pragma ide diagnostic ignored "OCUnusedGlobalDeclarationInspection"
namespace CTA {
namespace TargetCalib {

/* Use assumes amplitude range and number of points is
 * known from the beginning  */
TfMaker::TfMaker(const std::vector<float>& amplitudeV,
                 const size_t nTm, const size_t nCells) :
  fNtm(nTm),
  fNCells(nCells),
  fAmplitudeV(amplitudeV),
  fAmpIndex(0)
{

  if (fNCells == N_SAMPLINGCELL) {
    GetCell = &TfMaker::GetSamplingCell;
  } else if (fNCells == N_STORAGECELL) {
    GetCell = &TfMaker::GetStorageCell;
  } else {
    GERROR << "Invalid number of cells specified: " << fNCells;
  }

  Clear();
}

TfMaker::TfMaker(const std::string fileName) :
  fAmpIndex(0)
{
  GDEBUG << "Reading TFInput file: " << fileName;

  auto* cw = new CalibReadWriter();
  int status = cw->ReadTfInput(fileName, fAmplitudeV, fTfInput, fHits);
  if(status != TCAL_FILE_OK) {
    GERROR << "Error Saving Tf File: " << status;
  }
  delete cw;

  fNtm = fTfInput.size();
  fNCells = fTfInput[0][0].size();

  if (fNCells == N_SAMPLINGCELL) {
    GetCell = &TfMaker::GetSamplingCell;
  } else if (fNCells == N_STORAGECELL) {
    GetCell = &TfMaker::GetStorageCell;
  } else {
    GERROR << "TFInput file specifies invalid number of cells: " << fNCells;
  }

}


TfMaker::TfMaker(
  std::vector<float> amplitude,
  std::vector<std::vector<std::vector<std::vector<float>>>> tfinput,
  std::vector<std::vector<std::vector<std::vector<float>>>> hits
) : fAmplitudeV(std::move(amplitude)),
    fTfInput(std::move(tfinput)),
    fHits(std::move(hits)),
    fAmpIndex(0)
{
  fNtm = fTfInput.size();
  fNCells = fTfInput[0][0].size();

  if (fNCells == N_SAMPLINGCELL) {
    GetCell = &TfMaker::GetSamplingCell;
  } else if (fNCells == N_STORAGECELL) {
    GetCell = &TfMaker::GetStorageCell;
  } else {
    GERROR << "TFInput file specifies invalid number of cells: " << fNCells;
  }
}


void TfMaker::Clear() {
  GDEBUG << "Allocating tf memory... be patient";
  vector3_float pixV(N_TMPIX, vector2_float(fNCells,
                   std::vector<float>(fAmplitudeV.size(), 0.0)));
  fTfInput.clear();
  fHits.clear();
  fTfInput.resize(fNtm, pixV);
  fHits.resize(fNtm, pixV);
  GDEBUG << "Memory Allocated";
}

std::vector<int32_t> TfMaker::CreateADCStepVector(
  int32_t& adcMin, int32_t& adcMax,
  int32_t& adcMinSecondary, int32_t& adcMaxSecondary,
  uint16_t stepSize, uint16_t stepSizeSecondary
) {
  std::vector<int32_t> adcStepVector;

  // Pass through zero
  adcMin = (adcMin / stepSize - 1) * stepSize;
  adcMax = (adcMax / stepSize + 1) * stepSize;
  if (stepSizeSecondary > 0) {
    adcMinSecondary = adcMinSecondary / stepSizeSecondary * stepSizeSecondary;
    adcMaxSecondary = adcMaxSecondary / stepSizeSecondary * stepSizeSecondary;
  };

  int32_t s = adcMin, snew, ssize = stepSize;
  adcStepVector.push_back(adcMin);
  while (true) {
    snew = s + ssize;
    if (stepSizeSecondary > 0) {
      if (snew >= adcMinSecondary && snew <= adcMaxSecondary &&
          ssize == stepSize) {
        ssize = stepSizeSecondary;
        snew = adcMinSecondary;
      } else if (snew > adcMaxSecondary && ssize == stepSizeSecondary) {
        ssize = stepSize;
        snew = s + ssize;
      }
    }
    s = snew;
    adcStepVector.push_back(s);
    if (s >= adcMax) break;
  }
  adcMax = adcStepVector.back();
  return adcStepVector;
}

bool TfMaker::SetAmplitudeIndex(const float amplitude) {
#ifdef CHECM
  fSkipOverflow = amplitude > 2000;
#endif

  // Start with a guess
  if (fAmplitudeV[fAmpIndex] == amplitude) return true;
  if (fAmpIndex != fAmplitudeV.size()-1 &&
    fAmplitudeV[++fAmpIndex] == amplitude) return true;

  for (fAmpIndex=0; fAmpIndex<fAmplitudeV.size(); ++fAmpIndex){ // NOLINT;
    if (fAmplitudeV[fAmpIndex] == amplitude) return true;
  }
  GERROR << "Invalid amplitude value: " << amplitude;
  return false;
}

bool TfMaker::AddEvent(const float* wfs, const size_t nPix,
                       const size_t nSamples,
                       const uint16_t* fci, const size_t fciNPix) {

  if (nPix!=fciNPix) {
    GERROR << "Number of pixels does not match between arrays";
    return false;
  }
  for (size_t i=0; i<nPix; ++i) {
    auto* wf = (float*) (wfs + i*nSamples);
    auto tm = (uint16_t) (i / N_TMPIX);
    auto tmpix = (uint16_t) (i % N_TMPIX);
    if(!AddWaveform(wf, nSamples, tm, tmpix, fci[i])) {
      return false;
    }
  }
  return true;
}

bool TfMaker::AddWaveform(const float *wf, const size_t nSamples,
                          const uint16_t tm, const uint16_t tmpix,
                          const uint16_t fci) {

  for (uint16_t i=0; i<nSamples; ++i) {
    if(!AddSample(wf[i], i, tm, tmpix, fci)) {
      return false;
    }
  }

  return true;
}
  
bool TfMaker::AddSample(const float adc, const uint16_t sample,
                        const uint16_t tm, const uint16_t tmpix,
                        const uint16_t fci){

#ifdef CHECM
  if (fSkipOverflow && adc < 10) return true; // Don't include overflow samples
#endif

  uint16_t cell = (this->*GetCell)(fci, sample);
  float n = fHits[tm][tmpix][cell][fAmpIndex];
  float val = fTfInput[tm][tmpix][cell][fAmpIndex];
  fTfInput[tm][tmpix][cell][fAmpIndex] = val * (n /(n+1)) + adc/(n+1);
  fHits[tm][tmpix][cell][fAmpIndex]++;
  return true;
}

bool TfMaker::SaveTfInput(const std::string fileName){
  GDEBUG << "Writing File";
  bool fileOk = true;
  auto* cw = new CalibReadWriter();
  int status = cw->WriteTfInput(fileName, fAmplitudeV, fTfInput, fHits);
  if(status != TCAL_FILE_OK) {
    GERROR << "Error Saving Tf File: " << status;
    fileOk= false;
  }
  delete cw;
  return fileOk;
}

bool TfMaker::Save(const std::string fileName, const uint16_t adcStep,
                   const uint16_t adcStepSecondary,
                   const uint16_t amplitudeZero, const bool compress){

  if(!CheckHits(MIN_N_HITS)) {
    GWARNING << "Less than " << MIN_N_HITS  << " hits for at least 1 cell";
  }

  /* Save the TF flipping the axis */
  GDEBUG << "Finding ADC range";
  auto* adcMins = new float[fNtm * N_TMPIX * fNCells];
  auto* adcMaxs = new float[fNtm * N_TMPIX * fNCells];
  for (size_t tm=0; tm<fNtm; ++tm) {
    for (size_t tmpix=0; tmpix<N_TMPIX; ++tmpix) {
      for (size_t cell=0; cell<fNCells; ++cell) {
        size_t i = (tm * N_TMPIX + tmpix) * fNCells + cell;
        adcMins[i] = 9999;
        adcMaxs[i] = -9999;
        for (size_t pnt=0; pnt<fAmplitudeV.size(); ++pnt) {
          float adc = fTfInput[tm][tmpix][cell][pnt];
          if (adc<=adcMins[i]) adcMins[i] = adc;
          if (adc>=adcMaxs[i]) adcMaxs[i] = adc;
        }
      }
    }
  }
  int32_t adcMin_Min = 9999;
  int32_t adcMin_Max = -9999;
  int32_t adcMax_Min = 9999;
  int32_t adcMax_Max = -9999;
  for (size_t i=0; i<(fNtm * N_TMPIX * fNCells); ++i) {
    if (adcMins[i]<=adcMin_Min) adcMin_Min = (int32_t)adcMins[i];
    if (adcMins[i]>=adcMin_Max) adcMin_Max = (int32_t)(adcMins[i]+0.5);
    if (adcMaxs[i]<=adcMax_Min) adcMax_Min = (int32_t)adcMaxs[i];
    if (adcMaxs[i]>=adcMax_Max) adcMax_Max = (int32_t)(adcMaxs[i]+0.5);
  }
  delete[] adcMins;
  delete[] adcMaxs;

  int32_t adcMinSecondary = -50;
  int32_t adcMaxSecondary = 50;
  std::vector<int32_t> adcStepVector = CreateADCStepVector(
    adcMin_Min, adcMax_Max,
    adcMinSecondary, adcMaxSecondary,
    adcStep, adcStepSecondary
  );
  size_t nAdcPnts = adcStepVector.size();

  GDEBUG << "ADC Step = " << adcStep;
  GDEBUG << "ADC Min = " << adcMin_Min;
  GDEBUG << "ADC Max = " << adcMax_Max;
  GDEBUG << "Range of minimum ADC points across all pixels and cells: "
         << adcMin_Max - adcMin_Min;
  GDEBUG << "Range of maximum ADC points across all pixels and cells: "
         << adcMax_Max - adcMax_Min;
  if (adcMin_Min >= adcMax_Max) {
    GERROR << "Can not proceed, minimum adc is larger than maximum adc";
    return false;
  }
  GDEBUG << "N ADC POINTS = " << nAdcPnts;

  vector4_float tfFlip(fNtm, vector3_float(
    N_TMPIX, vector2_float(fNCells, std::vector<float>(nAdcPnts, 0.0)))
  );

  uint32_t broken_cells = 0;

  GDEBUG << "Flipping measured ADC and set Vped axis";
  for (uint16_t tm=0; tm<fNtm; ++tm) {
    for (uint16_t tmpix=0; tmpix<N_TMPIX; ++tmpix) {
      for (uint16_t cell=0; cell<fNCells; ++cell) {
        float adcMin, adcMax;
        bool broken = false;
        std::vector<float> cellTfInput(fTfInput[tm][tmpix][cell]);
        std::vector<float> cellAmplitude(fAmplitudeV);
        PrepareCellTFInput(adcMin, adcMax, broken, cellAmplitude, cellTfInput);
        if (!broken) {
          for (size_t pnt = 0; pnt < nAdcPnts; ++pnt) {
            int32_t adc = adcStepVector[pnt];
            tfFlip[tm][tmpix][cell][pnt] =
              GetAmplitude(adcMin, adcMax,
                           cellAmplitude, cellTfInput, adc) - amplitudeZero;
          }
        } else broken_cells++;
      }
    }
  }

  GDEBUG << "Number of broken cells in TM: " << broken_cells;

  GDEBUG << "Writing File " << fileName;
  bool fileOk = true;
  auto* cw = new CalibReadWriter();
  int status = cw->WriteTfData(fileName, adcStepVector, tfFlip, compress);
  if(status != TCAL_FILE_OK) {
    GERROR << "Error Saving Tf File: " << status;
    fileOk= false;
  }
  delete cw;
  return fileOk;
}

void TfMaker::PrepareCellTFInput(
  float& adcMin, float& adcMax, bool& broken,
  std::vector<float>& ampV, std::vector<float>& tfInput
){
  // Find max and min of tfInput
  adcMin = FLT_MAX;
  adcMax = -FLT_MAX;
  size_t iadcMin = 0;
  size_t iadcMax = 0;
  size_t halfsize = tfInput.size()/2;
  for (size_t i=0; i<tfInput.size(); ++i) {
    float adc1 = tfInput[i];
    if (adc1 >= adcMax && i > halfsize) {
      adcMax = adc1;
      iadcMax = i;
    }
    if (adc1 <= adcMin && i < halfsize) {
      adcMin = adc1;
      iadcMin = i;
    }
  }
  // Check if cell is broken
  if (adcMax - adcMin < 1000){
    broken = true;
    return;
  }
  // Remove entries that do not increase onto the next entry
  tfInput.erase(tfInput.begin() + iadcMax+1, tfInput.begin() + tfInput.size());
  ampV.erase(ampV.begin() + iadcMax+1, ampV.begin() + ampV.size());
  tfInput.erase(tfInput.begin(), tfInput.begin() + iadcMin);
  ampV.erase(ampV.begin(), ampV.begin() + iadcMin);
  size_t j = 0;
  while(true) {
    if (tfInput[j] > tfInput[j + 1]) {
      tfInput.erase(tfInput.begin() + j);
      ampV.erase(ampV.begin() + j);
    } else j++;
    if (j+1 > tfInput.size()-1) break;
  }
}

float TfMaker::GetAmplitude(
  const float adcMin, const float adcMax,
  const std::vector<float>& ampV, const std::vector<float>& tfInput,
  const int32_t adc
) {

  // adc is somewhere in the TF --> find surrounding
  // TF adcs and interpolate for amplitude
  if (adc>=adcMin && adc<=adcMax) {
    for (size_t i = 0; i < tfInput.size() - 1; ++i) {
      float adc1 = tfInput[i];
      float adc2 = tfInput[i + 1];
      if (adc >= adc1 && adc <= adc2) {
        float amp1 = ampV[i];
        float amp2 = ampV[i + 1];
        float amp_val = amp1 + (amp2 - amp1) * (adc - adc1) / (adc2 - adc1);
        return amp_val;
      }
    }
  }
  else if (adc < adcMin) {
    return ampV[0];
  }
  else if (adc > adcMax){
    return ampV.back();
  }
  else {
    GERROR << "No adc condition entered in GetAmplitude";
  }

  return 0;
}

bool TfMaker::CheckHits(const uint16_t thresh) {

  if (fHits.empty()) return false;

  float minHits = 65535;
  float maxHits = 0;

  for (size_t tm=0; tm<fNtm; ++tm){
    for (size_t tmpix=0; tmpix<N_TMPIX; ++tmpix){
      for (size_t cell=0; cell<fNCells; ++cell) {
        for (size_t pnt=0; pnt<fAmplitudeV.size(); ++pnt) {
          float hits = fHits[tm][tmpix][cell][pnt];
          if (minHits > hits) {
            minHits = hits;
          }
          else if (maxHits < hits) {
            maxHits = hits;
          }
        }
      }
    }
  }
  GDEBUG << "Min hits = " << minHits;
  GDEBUG << "Max hits = " << maxHits;
  return minHits >= thresh;
}

uint16_t TfMaker::GetSamplingCell(const uint16_t fci, const uint16_t sample) {
  auto cell = (uint16_t) ((fci + sample) % N_SAMPLINGCELL);
  return cell;
}

uint16_t TfMaker::GetStorageCell(const uint16_t fci, const uint16_t sample) {
  uint16_t row, column, blockphase;
  CalculateRowColumnBlockPhase(fci, row, column, blockphase);
  auto block = (uint16_t) (column * 8 + row);
  auto factor = (uint16_t) (64 * (1 - 2 * (block % 2)));
  auto shift = (uint16_t) ((((blockphase + sample) / 32) % 2) * factor);
  auto cell = (uint16_t) ((fci + sample + shift)%N_STORAGECELL);
  return cell;
}

}  // namespace TargetCalib
}  // namespace CTA

#pragma clang diagnostic pop