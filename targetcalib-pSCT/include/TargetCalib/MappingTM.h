#ifndef TARGETCALIB_MAPPINGTM_H
#define TARGETCALIB_MAPPINGTM_H

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

class MappingTM {
private:
  Mapping* fMapping;

  uint16_t fNModules;
  uint16_t fNRows;
  uint16_t fNColumns;

  std::vector<uint16_t> fSlot;
  std::vector<uint16_t> fRow; // Origin = bottom
  std::vector<uint16_t> fColumn; // Origin = left
  std::vector<double> fXPix; // X coordinate (m)
  std::vector<double> fYPix; // Y coordinate (m)
  std::vector<std::vector<uint16_t>> fContainedPixels;

public:
  explicit MappingTM(Mapping* mapping);
  void Recreate(Mapping* mapping);
  std::set<uint16_t> GetNeighbours(uint16_t superpixel, bool diagonals=false);
  double GetSize();

  uint16_t GetNModules(){return fNModules;}
  uint16_t GetNRows(){return fNRows;}
  uint16_t GetNColumns(){return fNColumns;}

  #define GETVTM(Title, Name, Type) \
	Type Get##Title(uint16_t slot) { \
    if (slot >= fNModules) { \
      GERROR << "Requested module (" << slot << ") is outside of the range " \
             << fNModules; \
    } \
    return (Name)[slot]; \
  } \
  std::vector<Type> Get##Title##Vector() { \
    return Name; \
  } \

  GETVTM(Slot, fSlot, uint16_t)
  GETVTM(Row, fRow, uint16_t)
  GETVTM(Column, fColumn, uint16_t)
  GETVTM(XPix, fXPix, double)
  GETVTM(YPix, fYPix, double)


  std::vector<uint16_t> GetContainedPixels(uint16_t slot){
    if (slot >= fNModules) {
      GERROR<<"Requested module ("<<slot<<") is outside of the range "<<fNModules;
    }
    return(fContainedPixels)[slot];
  }
  std::vector<std::vector<uint16_t>> GetContainedPixelsVector() {
    return fContainedPixels;
  }

};



}}

#endif //TARGETCALIB_MAPPINGTM_H
