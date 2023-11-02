#include "TargetCalib/MappingSP.h"
#include "TargetCalib/Mapping.h"

namespace CTA {
namespace TargetCalib {

MappingSP::MappingSP(Mapping* mapping) :
  fMapping(nullptr),
  fNSuperPixels(0),
  fNModules(0),
  fNRows(0),
  fNColumns(0)
{
  Recreate(mapping);
}

void MappingSP::Recreate(Mapping* mapping) {
  fMapping = mapping;
  uint16_t nSuperPixels = fMapping->GetNSuperPixels();
  fSuperPixel.assign(nSuperPixels, 0);
  fSlot.assign(nSuperPixels, 0);
  fASIC.assign(nSuperPixels, 0);
  fTMSP.assign(nSuperPixels, 0);
  fRow.assign(nSuperPixels, 0);
  fColumn.assign(nSuperPixels, 0);
  fXPix.assign(nSuperPixels, 0.);
  fYPix.assign(nSuperPixels, 0.);
  std::vector<uint16_t> empty;
  fContainedPixels.assign(nSuperPixels, empty);

  std::vector<uint16_t> n;
  n.assign(nSuperPixels, 0);

  for (uint16_t p = 0; p < fMapping->GetNPixels(); ++p) {
    uint16_t superpixel = fMapping->GetSuperPixel(p);
    n[superpixel] += 1;
    fSuperPixel[superpixel] = superpixel;
    fSlot[superpixel] = fMapping->GetSlot(p);
    fASIC[superpixel] = fMapping->GetASIC(p);
    fTMSP[superpixel] = superpixel % fNTMSP;
    fRow[superpixel] = uint16_t(fMapping->GetRow(p) / 2);
    fColumn[superpixel] = uint16_t(fMapping->GetColumn(p) / 2);
    fXPix[superpixel] += fMapping->GetXPix(p);
    fYPix[superpixel] += fMapping->GetYPix(p);
    fContainedPixels[superpixel].push_back(p);
  }
  for (uint16_t sp = 0; sp < nSuperPixels; ++sp) {
    fXPix[sp] /= n[sp];
    fYPix[sp] /= n[sp];
  }

  std::set<uint16_t> spSet(fSuperPixel.begin(), fSuperPixel.end());
  std::set<uint16_t> moduleSet(fSlot.begin(), fSlot.end());
  std::set<uint16_t> rowSet(fRow.begin(), fRow.end());
  std::set<uint16_t> colSet(fColumn.begin(), fColumn.end());

  fNSuperPixels = (uint16_t) spSet.size();
  fNModules = (uint16_t) moduleSet.size();
  fNRows = (uint16_t) rowSet.size();
  fNColumns = (uint16_t) colSet.size();
}

std::set<uint16_t> MappingSP::GetNeighbours(uint16_t superpixel,bool diagonals){

  if (superpixel >= fNSuperPixels) {
    GERROR<< "Requested superpixel (" << superpixel
          << ") is outside of the range " << fNSuperPixels;
  }

  uint16_t row = fRow[superpixel];
  uint16_t col = fColumn[superpixel];
  std::set<uint16_t> neighbours;

  for (uint16_t p = 0; p < fNSuperPixels; ++p) {
    if (p == superpixel) continue;
    int row_sep = abs((int) row - (int) fRow[p]);
    int col_sep = abs((int) col - (int) fColumn[p]);

    if (row_sep <= 1 && col_sep <= 1) {
      if (diagonals) neighbours.insert(p);
      else if (!(row_sep == 1 && col_sep == 1)) neighbours.insert(p);
    }
  }
  return neighbours;
}

double MappingSP::GetSize() {
  return fMapping->GetSize() * 2;
}

}}

