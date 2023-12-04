// Copyright (c) 2016 The CTA Consortium. All rights reserved.
#include "TargetCalib/PedestalMaker.h"

namespace CTA {
namespace TargetCalib {

PedestalMaker::PedestalMaker(const uint16_t nTm, const uint16_t nBlocks,
                             const uint16_t nSamples, const bool diagnostic) :
  fNtm(nTm),
  fNBlocks(nBlocks),
  fNSamples(nSamples),
  fNSamplesBP((uint16_t) (N_BLOCKPHASE + nSamples - 1)),
  fDiagnostic(diagnostic),
  fMinHits(-1),
  fMaxHits(-1),
  fMinSamplesBP(0),
  fMaxSamplesBP(0)
{
  Clear();
}

void PedestalMaker::Clear() {
  GDEBUG << "Allocating pedestal memory... be patient";
  vector3_float pixV(N_TMPIX, vector2_float(fNBlocks,
                     std::vector<float>(fNSamplesBP, 0.0)));
  fPed.clear();
  fHits.clear();
  fPed.resize(fNtm, pixV);
  fHits.resize(fNtm, pixV);
  fBlockphases.clear();
  if (fDiagnostic){
    fPed2.clear();
    fStd.clear();
    fPed2.resize(fNtm, pixV);
    fStd.resize(fNtm, pixV);
  }
  GDEBUG << "Memory Allocated";
}

bool PedestalMaker::AddEvent(const uint16_t* wfs, const size_t nPix,
                             const size_t nSamples,
                             const uint16_t* fci, const size_t fciNPix) {

  if (nPix!=fciNPix) {
    GERROR << "Number of pixels does not match between arrays";
    return false;
  }
  uint16_t row, column, blockPhase;
  for (size_t i=0; i<nPix; ++i) {
    CalculateRowColumnBlockPhase(fci[i], row, column, blockPhase);
    auto* wf = (uint16_t*) (wfs + i*nSamples);
    auto tm = (uint16_t) (i / N_TMPIX);
    auto tmpix = (uint16_t) (i % N_TMPIX);
    auto block = (uint16_t) (row + column * N_ROWS);
    if(!AddWaveform(wf, nSamples, tm, tmpix, block, blockPhase)) {
      return false;
    }
  }
  return true;
}

bool PedestalMaker::AddWaveform(const uint16_t* wf, const size_t nSamples,
                                const uint16_t tm, const uint16_t tmpix,
                                const uint16_t blk,
                                const uint16_t blkPhase){

  for (uint16_t i=0; i<nSamples; ++i) {
    if(!AddSample(wf[i], i, tm, tmpix, blk, blkPhase)) {
      return false;
    }
  }
  return true;
}

bool PedestalMaker::AddSample(const uint16_t adc, const uint16_t sample,
                              const uint16_t tm, const uint16_t tmpix,
                              const uint16_t blk, const uint16_t blkPhase){

  fBlockphases.insert(blkPhase);
  uint16_t sampleBP = blkPhase + sample;

  float* ped = &fPed[tm][tmpix][blk][sampleBP];
  float* hits = &fHits[tm][tmpix][blk][sampleBP];
  float delta = adc - *ped;
  *hits += 1.0;
  *ped += delta / *hits;

  if (fDiagnostic) {
    float *m2 = &fPed2[tm][tmpix][blk][sampleBP];
    float *std = &fStd[tm][tmpix][blk][sampleBP];
    float delta2 = adc - *ped;
    *m2 += delta * delta2;
    *std = sqrtf(*m2 / (*hits - 1));
  }

  return true;
}
  
bool PedestalMaker::Save(const std::string& fileName, const bool compress){
  if(!CheckHits(MIN_N_HITS)) {
    GWARNING << "Less than " << MIN_N_HITS  << " hits for at least 1 cell";
  }

  std::map<std::string, float> header;
  header["MINHITS"] = fMinHits;
  header["MAXHITS"] = fMaxHits;
  header["MINSAMPLESBP"] = fMinSamplesBP;
  header["MAXSAMPLESBP"] = fMaxSamplesBP;

  GDEBUG << "Saving file with compression on/off =  " << compress;

  bool fileOk = true;
  auto* cw = new CalibReadWriter();
  int status;
  if (fDiagnostic)
    status=cw->WritePedestalData(fileName, fPed, fHits, fStd, compress);
  else status=cw->WritePedestalData(fileName, fPed, compress);
  cw->WriteHeader(header);

  if(status!=TCAL_FILE_OK) {
    GERROR << "Error Saving PedestalMaker File";
    fileOk = false;
    delete cw;
  }
  delete cw;
  return fileOk;
}

bool PedestalMaker::CheckHits(const uint16_t thresh) {

  if (fHits.empty()) return false;

  std::ostringstream oss;
  std::copy(fBlockphases.begin(), fBlockphases.end(),
            std::ostream_iterator<int>(oss, " "));
  std::string bpStr = oss.str();
  GDEBUG << "Available blockphases: " << bpStr;

  float minHits = 65535;
  float maxHits = 0;
  uint16_t minBP = *fBlockphases.begin();
  uint16_t maxBP = *fBlockphases.rbegin();
  uint16_t minSamplesBP = minBP;
  uint16_t maxSamplesBP = maxBP + fNSamples - 1;

  for (size_t tm=0; tm<fNtm; ++tm) {
    for (size_t tmpix=0; tmpix<N_TMPIX; ++tmpix) {
      for (size_t blk=0; blk<fNBlocks; ++blk) {
        for (size_t sampBP=minSamplesBP; sampBP<=maxSamplesBP; ++sampBP) {
          float hits = fHits[tm][tmpix][blk][sampBP];
          if (hits == 0) {
            GWARNING << "0 hits in;" << tm << ", " << tmpix << ", " << blk << ", " << sampBP;
          }
          else if (minHits > hits) minHits = hits;
          else if (maxHits < hits) maxHits = hits;
        }
      }
    }
  }
  fMinHits = minHits;
  fMaxHits = maxHits;
  fMinSamplesBP = minSamplesBP;
  fMaxSamplesBP = maxSamplesBP;
  GDEBUG << "Min hits = " << minHits;
  GDEBUG << "Max hits = " << maxHits;
  return minHits >= thresh;
}
  
}  // namespace TargetCalib
}  // namespace CTA
