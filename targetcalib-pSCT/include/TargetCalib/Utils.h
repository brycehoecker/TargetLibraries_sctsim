// Copyright (c) 2016 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains utility functions used by the calibration library
 */
#ifndef TARGETCALIB_UTILS_H
#define TARGETCALIB_UTILS_H

#include "TargetCalib/Constants.h"
#include "TargetCalib/Logger.h"
#include "TargetDriver/DataPacket.h"

#include <iostream>

namespace CTA {
namespace TargetCalib {

typedef std::vector<std::vector<float>> vector2_float;
typedef std::vector<vector2_float> vector3_float;
typedef std::vector<vector3_float> vector4_float;
typedef std::vector<std::vector<uint16_t >> vector2_uint16;
typedef std::vector<vector2_uint16> vector3_uint16;
typedef std::vector<vector3_uint16> vector4_uint16;

static std::string GetEnv(const char* envvar)
{
  const char *dir = std::getenv(envvar);
  if (!dir) {
    GERROR << envvar << " has not been defined in this environment";
    return std::string();
  }
  return std::string(dir);
}

static void PrintProgress(float progress = 0.0) {
  int barWidth = 70;
  std::cout << "[";
  int pos = (int) (barWidth * progress);
  for (int i = 0; i < barWidth; ++i) {
    if (i < pos) std::cout << "=";
    else if (i == pos) std::cout << ">";
    else std::cout << " ";
  }
  std::cout << "] " << int(progress * 100.0) << " %\r";
  std::cout.flush();
}

static void CalculateRowColumnBlockPhase(
  uint16_t pCellId,
  uint16_t& pRow,
  uint16_t& pColumn,
  uint16_t& pBlockPhase
)
{
  using CTA::TargetDriver::DataPacket;
  DataPacket::CalculateRowColumnBlockPhase(pCellId, pRow, pColumn, pBlockPhase);
}

static void CalculateRowColumnBlockPhase(
  const uint16_t* pCellId, const size_t sizeCellID,
  uint16_t* pRow,
  uint16_t* pColumn,
  uint16_t* pBlockPhase
)
{
  using CTA::TargetDriver::DataPacket;
  for (uint64_t i=0; i<sizeCellID; ++i) {
    CalculateRowColumnBlockPhase(pCellId[i], pRow[i],
                                 pColumn[i], pBlockPhase[i]);
  }
}


static uint16_t GetCellIDTC(uint16_t block, uint16_t blockphase,
                            uint16_t sample) {
  auto firstCellID = (uint16_t) (block * N_BLOCKPHASE + blockphase);
  auto factor = (uint16_t) (64 * (1 - 2 * (block % 2)));
  auto shift = (uint16_t) ((((blockphase + sample) / 32) % 2) * factor);
  auto cell = (uint16_t) ((firstCellID + sample + shift) % N_STORAGECELL);
  return cell;
}

static uint16_t GetCellIDTC(uint16_t row, uint16_t column, uint16_t blockphase,
                          uint16_t sample) {
  auto block = (uint16_t) (column * 8 + row);
  return GetCellIDTC(block, blockphase, sample);
}

static uint16_t GetCellIDTC(uint16_t firstCellID, uint16_t sample) {
  uint16_t row, column, blockphase;
  CalculateRowColumnBlockPhase(firstCellID, row, column, blockphase);
  return GetCellIDTC(row, column, blockphase, sample);
}

static void GetCellIDTCArray(
  const uint16_t* firstCellID, const size_t sizeFirstCellID,
  const uint16_t* sample, const size_t sizeSample,
  uint16_t* cellID
)
{
  if (sizeFirstCellID!=sizeSample) {
    GERROR << "Size of arrays do not match";
    return;
  }

  for (uint64_t i = 0; i < sizeSample; ++i) {
    cellID[i] = GetCellIDTC(firstCellID[i], sample[i]);
  }
}

static void GetCellIDTCArray(
  const uint16_t firstCellID,
  const uint16_t* sample, const size_t sizeSample,
  uint16_t* cellID
)
{
  for (uint64_t i = 0; i < sizeSample; ++i) {
    cellID[i] = GetCellIDTC(firstCellID, sample[i]);
  }
}


static std::string GetTFPath(int16_t sn) {
  std::string tfBaseDir = GetEnv("TC_CONFIG_PATH");
  std::string tfBasePath = tfBaseDir + "/SN%04d_tf.tcal";
  uint64_t nChar = tfBasePath.length() + 10;
  if (sn >= 0) {
    char path[nChar];
    sprintf(path, tfBasePath.c_str(), sn);
    if (std::ifstream(path)) {
      return std::string(path);
    }
  }
  return "";
}


}  // namespace TargetCalib
}  // namespace CTA
#endif //TARGETCALIB_UTILS_H
