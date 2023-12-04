#include "TargetCalib/MappingTM.h"
#include "TargetCalib/Mapping.h"

namespace CTA {
namespace TargetCalib {

MappingTM::MappingTM(Mapping* mapping) :
  fMapping(nullptr),
  fNModules(0),
  fNRows(0),
  fNColumns(0)
{
  Recreate(mapping);
}

void MappingTM::Recreate(Mapping* mapping) {
  fMapping = mapping;
  uint16_t nModules = fMapping->GetNModules();
  fSlot.assign(nModules, 0);
  fRow.assign(nModules, 0);
  fColumn.assign(nModules, 0);
  fXPix.assign(nModules, 0.);
  fYPix.assign(nModules, 0.);
  std::vector<uint16_t> empty;
  fContainedPixels.assign(nModules, empty);

  std::vector<uint16_t> n;
  n.assign(nModules, 0);

  for (uint16_t p = 0; p < fMapping->GetNPixels(); ++p) {
    uint16_t slot = fMapping->GetSlot(p);
    n[slot] += 1;
    fSlot[slot] = slot;
    fRow[slot] = uint16_t(fMapping->GetRow(p) / 2);
    fColumn[slot] = uint16_t(fMapping->GetColumn(p) / 2);
    fXPix[slot] += fMapping->GetXPix(p);
    fYPix[slot] += fMapping->GetYPix(p);
    fContainedPixels[slot].push_back(p);
  }
  for (uint16_t sp = 0; sp < nModules; ++sp) {
    fXPix[sp] /= n[sp];
    fYPix[sp] /= n[sp];
  }

  std::set<uint16_t> moduleSet(fSlot.begin(), fSlot.end());
  std::set<uint16_t> rowSet(fRow.begin(), fRow.end());
  std::set<uint16_t> colSet(fColumn.begin(), fColumn.end());

  fNModules = (uint16_t) moduleSet.size();
  fNRows = (uint16_t) rowSet.size();
  fNColumns = (uint16_t) colSet.size();
}

std::set<uint16_t> MappingTM::GetNeighbours(uint16_t slot ,bool diagonals){

  if (slot >= fNModules) {
    GERROR<< "Requested module (" << slot
          << ") is outside of the range " << fNModules;
  }

  uint16_t row = fRow[slot];
  uint16_t col = fColumn[slot];
  std::set<uint16_t> neighbours;

  for (uint16_t p = 0; p < fNModules; ++p) {
    if (p == slot) continue;
    int row_sep = abs((int) row - (int) fRow[p]);
    int col_sep = abs((int) col - (int) fColumn[p]);

    if (row_sep <= 1 && col_sep <= 1) {
      if (diagonals) neighbours.insert(p);
      else if (!(row_sep == 1 && col_sep == 1)) neighbours.insert(p);
    }
  }
  return neighbours;
}

double MappingTM::GetSize() {
  return fMapping->GetSize() * 8;
}

}}

