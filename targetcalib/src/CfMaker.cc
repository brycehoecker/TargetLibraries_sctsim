// Copyright (c) 2016 The CTA Consortium. All rights reserved.
#include "TargetCalib/CfMaker.h"
#include "TargetCalib/CalibReadWriter.h"

#include <cmath>
#include <iostream>
#include <sstream>
#include <vector>

namespace CTA {
namespace TargetCalib {

CfMaker::CfMaker(const uint16_t nTm) {
  fNtm = nTm;
  Clear();
}

void CfMaker::Clear() {
  fCf.clear();
  std::vector<float> pixV(N_TMPIX, 0.0);
  fCf.resize(fNtm, pixV);
}
  
bool CfMaker::Set(const uint16_t tm, const uint16_t tmpix, float cf){
  if(!CheckBounds(tm,tmpix)) return false;
  fCf[tm][tmpix] = cf;
  return true;
}

bool CfMaker::SetAll(const float* cf, const size_t cfSize) {
  for (size_t i=0; i<cfSize; ++i) {
    uint16_t tm = (uint16_t) (i / N_TMPIX);
    uint16_t tmpix = (uint16_t) (i % N_TMPIX);
    if(!Set(tm, tmpix, cf[i])) return false;
  }
  return true;
}

bool CfMaker::SetAll(const uint16_t* tm, const size_t tmSize,
                       const uint16_t* tmpix, const size_t tmpixSize,
                       const float* cf, const size_t cfSize) {

  if (cfSize!=tmSize || cfSize!=tmpixSize) {
    GERROR << "Number of pixels does not match between arrays";
   return false;
  }
  for (size_t i=0; i<cfSize; ++i) {
    if(!Set(tm[i], tmpix[i], cf[i])) return false;
  }
  return true;
}
  

bool CfMaker::Save(const std::string fileName, const bool compress){

  bool fileOk = true;
  CalibReadWriter* cw = new CalibReadWriter();
  if(cw->WriteCfData(fileName, fCf, compress)!=TCAL_FILE_OK) {
    GERROR << "Error Saving CfMaker File";
    fileOk= false;
  }
  delete cw;
  return fileOk;
}
bool CfMaker::CheckBounds(uint16_t tm, uint16_t tmpix) {

  bool ok = true;
  if(tm>=fNtm) {
    GERROR << "Invalid tm " << tm << " (" << fNtm << ")";
    ok = false;
  }
    
  if(tmpix>=N_TMPIX) {
    GERROR << "Invalid pixel " << tmpix << " (" << N_TMPIX << ")";
    ok = false;
  }
  return ok;
}
 
}  // namespace TargetCalib
}  // namespace CTA
