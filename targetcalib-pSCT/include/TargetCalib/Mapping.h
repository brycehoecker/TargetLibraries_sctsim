//
// Created by Jason Watson on 12/11/2017.
//

#ifndef TARGETCALIB_MAPPING_H
#define TARGETCALIB_MAPPING_H

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
#include "TargetCalib/MappingSP.h"
#include "TargetCalib/MappingTM.h"

namespace CTA {
namespace TargetCalib {

class Mapping {
private:
  std::string fPath;
  bool fSingleModule;
  uint16_t fNPixels;
  uint16_t fNModules;
  uint16_t fNTMPix = 64;
  uint16_t fNRows;
  uint16_t fNColumns;
  uint16_t fNSuperPixels;

  std::vector<uint16_t> fPixel;
  std::vector<uint16_t> fSlot;
  std::vector<uint16_t> fASIC;
  std::vector<uint16_t> fChannel;
  std::vector<uint16_t> fTMPixel;
  std::vector<uint16_t> fRow; // Origin = bottom
  std::vector<uint16_t> fColumn; // Origin = left
  std::vector<uint16_t> fSipmPix; // Hamamatsu quoted pixel
  std::vector<uint16_t> fTriggerPatch;
  std::vector<uint16_t> fHVPatch;
  std::vector<uint16_t> fSuperPixel;
  std::vector<double> fXPix; // X coordinate (m)
  std::vector<double> fYPix; // Y coordinate (m)

  MappingSP* fMappingSP = nullptr;
  MappingTM* fMappingTM = nullptr;

  void LoadConfig(std::string cfgPath, bool singleModule=false);
  void Rotate(uint16_t& row, uint16_t& col, double& xpix, double& ypix);

public:
  explicit Mapping(std::string cfgPath, bool singleModule=false);
  ~Mapping() {
    delete fMappingSP;
    fMappingSP = nullptr;
    delete fMappingTM;
    fMappingTM = nullptr;
  }
  void Rotate(uint16_t rotation);
  void CreateASCII(std::string filepath);
  std::set<uint16_t> GetNeighbours(uint16_t pixel, bool diagonals=false);
  double GetSize();

  std::string GetCfgPath(){return fPath;}
  bool IsSingleModule(){return fSingleModule;}
  uint16_t GetNPixels(){return fNPixels;}
  uint16_t GetNModules(){return fNModules;}
  uint16_t GetNTMPix(){return fNTMPix;}
  uint16_t GetNRows(){return fNRows;}
  uint16_t GetNColumns(){return fNColumns;}
  uint16_t GetNSuperPixels(){return fNSuperPixels;}

  MappingSP* GetMappingSP() {
    if (fMappingSP == nullptr) fMappingSP = new MappingSP(this);
    return fMappingSP;
  }

  MappingTM* GetMappingTM() {
    if (fMappingTM == nullptr) fMappingTM = new MappingTM(this);
    return fMappingTM;
  }

#define GETV(Title, Name, Type) \
	Type Get##Title(uint16_t pixel) { \
    if (pixel >= fNPixels) { \
      GERROR << "Requested pixel (" << pixel << ") is outside of the range " \
             << fNPixels; \
    } \
    return (Name)[pixel]; \
  } \
  std::vector<Type> Get##Title##Vector() { \
    return Name; \
  } \

  GETV(Pixel, fPixel, uint16_t)
  GETV(Slot, fSlot, uint16_t)
  GETV(ASIC, fASIC, uint16_t)
  GETV(Channel, fChannel, uint16_t)
  GETV(TMPixel, fTMPixel, uint16_t)
  GETV(Row, fRow, uint16_t)
  GETV(Column, fColumn, uint16_t)
  GETV(SipmPix, fSipmPix, uint16_t)
//  GETV(TriggerPatch, fTriggerPatch, uint16_t)
//  GETV(HVPatch, fHVPatch, uint16_t)
  GETV(SuperPixel, fSuperPixel, uint16_t)
  GETV(XPix, fXPix, double)
  GETV(YPix, fYPix, double)

  uint16_t GetTriggerPatch(uint16_t pixel){
    GWARNING << "TriggerPatch has been deprecated, please switch to SuperPixel";
    if (pixel >= fNPixels) {
      GERROR<<"Requested pixel ("<<pixel<<") is outside of the range "<<fNPixels;
    }
    return(fTriggerPatch)[pixel];
  }
  std::vector<uint16_t> GetTriggerPatchVector() {
    GWARNING << "TriggerPatch has been deprecated, please switch to SuperPixel";
    return fTriggerPatch;
  }
  uint16_t GetHVPatch(uint16_t pixel){
    GWARNING << "HVPatch has been deprecated, please switch to SuperPixel";
    if (pixel >= fNPixels) {
      GERROR<<"Requested pixel ("<<pixel<<") is outside of the range "<<fNPixels;
    }
    return(fHVPatch)[pixel];
  }
  std::vector<uint16_t> GetHVPatchVector() {
    GWARNING << "HVPatch has been deprecated, please switch to SuperPixel";
    return fHVPatch;
  }


  // Coordinates for plotting ON-Telescope UP frame arrow
  uint16_t fOTUpRow_l = 41;
  uint16_t fOTUpRow_u = 46;
  uint16_t fOTUpCol_l = 44;
  uint16_t fOTUpCol_u = 44;
  double fOTUpX_l = 0.1298;
  double fOTUpX_u = 0.1298;
  double fOTUpY_l = 0.117;
  double fOTUpY_u = 0.149;

  void as_dataframe() {
    GERROR << "Mapping::as_dataframe is a python-only function overloaded "
        "inside target_calib.i";
  }

};


}}

#endif //TARGETCALIB_MAPPING_H
