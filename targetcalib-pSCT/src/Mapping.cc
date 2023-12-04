//
// Created by Jason Watson on 12/11/2017.
//

#include <utility>
#include <algorithm>

#include "TargetCalib/Mapping.h"

namespace CTA {
namespace TargetCalib {

Mapping::Mapping(std::string cfgPath, bool singleModule) :
  fPath(std::move(cfgPath)),
  fSingleModule(singleModule),
  fNPixels(0),
  fNModules(0),
  fNRows(0),
  fNColumns(0)
{
  LoadConfig(fPath, fSingleModule);
}

void Mapping::LoadConfig(std::string cfgPath, bool singleModule) {
  GINFO << "Loading Mapping Config: " << cfgPath;
  std::ifstream infile(cfgPath);
  if (!infile.is_open())
    GERROR << "Cannot find module config file: " << cfgPath;

  std::string str;
  std::getline(infile, str); // skip the first line

  std::string l;
  uint16_t pixel, slot, asic, ch, tmpix, row, col, sipmPix, trigger, hv, superpixel;
  double xpix, ypix;
  while (infile >> pixel >> slot >> asic >> ch >> tmpix >> row >> col
                >> sipmPix >> trigger >> hv >> superpixel >> xpix >> ypix) {
    if (singleModule && fNPixels >= fNTMPix) break;
    fNPixels++;
    fPixel.push_back(pixel);
    fSlot.push_back(slot);
    fASIC.push_back(asic);
    fChannel.push_back(ch);
    fTMPixel.push_back(tmpix);
    fRow.push_back(row);
    fColumn.push_back(col);
    fSipmPix.push_back(sipmPix);
    fTriggerPatch.push_back(trigger);
    fHVPatch.push_back(hv);
    fSuperPixel.push_back(superpixel);
    fXPix.push_back(xpix);
    fYPix.push_back(ypix);
  }
  infile.close();

  if (singleModule){
    double avgX=0, avgY=0;
    uint16_t minRow=65535, minCol=65535;
    for (size_t i=0; i<fNPixels; ++i) {
      avgX += fXPix[i];
      avgY += fYPix[i];
      if (minRow > fRow[i]) minRow = fRow[i];
      if (minCol > fColumn[i]) minCol = fColumn[i];
    }
    avgX /= fNPixels;
    avgY /= fNPixels;

    for (size_t i=0; i<fNPixels; ++i) {
      fXPix[i] -= avgX;
      fYPix[i] -= avgY;
      fRow[i] -= minRow;
      fColumn[i] -= minCol;
    }
  }

  std::set<uint16_t> moduleSet(fSlot.begin(), fSlot.end());
  std::set<uint16_t> rowSet(fRow.begin(), fRow.end());
  std::set<uint16_t> colSet(fColumn.begin(), fColumn.end());
  std::set<uint16_t> spSet(fSuperPixel.begin(), fSuperPixel.end());

  fNModules = (uint16_t) moduleSet.size();
  fNRows = (uint16_t) rowSet.size();
  fNColumns = (uint16_t) colSet.size();
  fNSuperPixels = (uint16_t) spSet.size();
}



void Mapping::Rotate(uint16_t& row, uint16_t& col, double& xpix, double& ypix) {
  uint16_t r = row;
  uint16_t c = col;
  double x = xpix;
  double y = ypix;
  row = (uint16_t) (fNColumns - 1 - c);
  col = r;
  xpix = y;
  ypix = -x;
}

void Mapping::Rotate(uint16_t rotation) {
  if (rotation) {
    rotation = (uint16_t) (rotation % 4);
    for (uint16_t pix = 0; pix < fNPixels; ++pix) {
      for (uint16_t r=0; r < rotation; ++r) {
        Rotate(fRow[pix], fColumn[pix], fXPix[pix], fYPix[pix]);
      }
    }
    Rotate(fOTUpRow_l, fOTUpCol_l, fOTUpX_l, fOTUpY_l);
    Rotate(fOTUpRow_u, fOTUpCol_u, fOTUpX_u, fOTUpY_u);
  }
  if (fMappingSP != nullptr) fMappingSP->Recreate(this);
  if (fMappingTM != nullptr) fMappingTM->Recreate(this);
}

void Mapping::CreateASCII(std::string filepath) {
  std::ofstream outfile(filepath);
  if (!outfile.is_open())
    GERROR << "Cannot create file: " << filepath;
    GINFO << "Created ASCII: " << filepath << std::endl;

  outfile << "pixel" << '\t'
          << "slot" << '\t'
          << "asic" << '\t'
          << "channel" << '\t'
          << "tmpix" << '\t'
          << "row" << '\t'
          << "col" << '\t'
          << "sipmpix" << '\t'
          << "triggerpatch" << '\t'
          << "hvpatch" << '\t'
          << "superpixel" << '\t'
          << "xpix" << '\t'
          << "ypix" << "\n";
  for (uint16_t p=0; p<fNPixels; ++p) {
    outfile << fPixel[p] << '\t'
            << fSlot[p] << '\t'
            << fASIC[p] << '\t'
            << fChannel[p] << '\t'
            << fTMPixel[p] << '\t'
            << fRow[p] << '\t'
            << fColumn[p] << '\t'
            << fSipmPix[p] << '\t'
            << fTriggerPatch[p] << '\t'
            << fHVPatch[p] << '\t'
            << fSuperPixel[p] << '\t'
            << fXPix[p] << '\t'
            << fYPix[p] << "\n";
  }
  outfile.close();
}

std::set<uint16_t> Mapping::GetNeighbours(uint16_t pixel, bool diagonals){

  if (pixel >= fNPixels) {
    GERROR<<"Requested pixel ("<<pixel<<") is outside of the range "<<fNPixels;
  }

  uint16_t row = fRow[pixel];
  uint16_t col = fColumn[pixel];
  std::set<uint16_t> neighbours;

  for (uint16_t p = 0; p < fNPixels; ++p) {
    if (p == pixel) continue;
    int row_sep = abs((int) row - (int) fRow[p]);
    int col_sep = abs((int) col - (int) fColumn[p]);

    if (row_sep <= 1 && col_sep <= 1) {
      if (diagonals) neighbours.insert(p);
      else if (!(row_sep == 1 && col_sep == 1)) neighbours.insert(p);
    }
  }
  return neighbours;
}

double Mapping::GetSize() {
  auto row = uint16_t(fNRows / 2);
  std::vector<double> xpix;
  for (uint16_t p = 0; p < fNPixels; ++p) {
    if (fRow[p] == row) xpix.push_back(fXPix[p]);
  }
  std::sort(xpix.begin(), xpix.end());
  double minSep = 99999;
  for (size_t i = 0; i < xpix.size()-1; ++i) {
    double sep = xpix[i+1] - xpix[i];
    if (minSep > sep) minSep = sep;
  }
  return minSep;
}

}}

