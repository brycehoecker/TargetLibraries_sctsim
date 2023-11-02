#ifndef TARGETCALIB_MAPPINGSP_H
#define TARGETCALIB_MAPPINGSP_H

#include <cstdint>
#include <string>
#include <cstdlib>
#include <cmath>
#include <fstream>
#include <sstream>
#include <iostream>
#include <vector>
#include <set>
#include "TargetCalib/Logger.h"

namespace CTA {
namespace TargetCalib {

class Mapping;

class MappingSP {
private:
  Mapping* fMapping;

  uint16_t fNSuperPixels;
  uint16_t fNModules;
  uint16_t fNTMSP = 16;
  uint16_t fNRows;
  uint16_t fNColumns;

  std::vector<uint16_t> fSuperPixel;
  std::vector<uint16_t> fSlot;
  std::vector<uint16_t> fASIC;
  std::vector<uint16_t> fTMSP;
  std::vector<uint16_t> fRow; // Origin = bottom
  std::vector<uint16_t> fColumn; // Origin = left
  std::vector<double> fXPix; // X coordinate (m)
  std::vector<double> fYPix; // Y coordinate (m)
  std::vector<std::vector<uint16_t>> fContainedPixels;

public:
  explicit MappingSP(Mapping* mapping);
  void Recreate(Mapping* mapping);
  std::set<uint16_t> GetNeighbours(uint16_t superpixel, bool diagonals=false);
  double GetSize();

  uint16_t GetNSuperPixels(){return fNSuperPixels;}
  uint16_t GetNModules(){return fNModules;}
  uint16_t GetNTMSP(){return fNTMSP;}
  uint16_t GetNRows(){return fNRows;}
  uint16_t GetNColumns(){return fNColumns;}

  #define GETVSP(Title, Name, Type) \
	Type Get##Title(uint16_t superpixel) { \
    if (superpixel >= fNSuperPixels) { \
      GERROR << "Requested pixel (" << superpixel << ") is outside of the range " \
             << fNSuperPixels; \
    } \
    return (Name)[superpixel]; \
  } \
  std::vector<Type> Get##Title##Vector() { \
    return Name; \
  } \

  GETVSP(SuperPixel, fSuperPixel, uint16_t)
  GETVSP(Slot, fSlot, uint16_t)
  GETVSP(ASIC, fASIC, uint16_t)
  GETVSP(TMSP, fTMSP, uint16_t)
  GETVSP(Row, fRow, uint16_t)
  GETVSP(Column, fColumn, uint16_t)
  GETVSP(XPix, fXPix, double)
  GETVSP(YPix, fYPix, double)


  std::vector<uint16_t> GetContainedPixels(uint16_t superpixel){
    if (superpixel >= fNSuperPixels) {
      GERROR<<"Requested superpixel ("<<superpixel<<") is outside of the range "<<fNSuperPixels;
    }
    return(fContainedPixels)[superpixel];
  }
  std::vector<std::vector<uint16_t>> GetContainedPixelsVector() {
    return fContainedPixels;
  }

};



}}

#endif //TARGETCALIB_MAPPINGSP_H
