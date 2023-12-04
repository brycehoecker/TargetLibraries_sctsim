// Copyright (c) 2016 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains constants used by the calibration library
 */
#ifndef INCLUDE_TARGETCALIB_CONSTANTS_H_
#define INCLUDE_TARGETCALIB_CONSTANTS_H_

namespace CTA {
namespace TargetCalib {
#ifndef SCT
  #define CHECS
#endif
//#define CHECM
//#define SCT

#define N_TM_MAX 225
#define N_TMPIX 64
#define N_SAMPLINGCELL 64
//#define N_STORAGECELL 4096
#ifdef SCT
  #define N_STORAGECELL 16384
#else
  #define N_STORAGECELL 4096
#endif
#define N_BLOCKPHASE 32
#define MIN_N_HITS 10
#define T_SAMPLES_PER_WAVEFORM_BLOCK 32
#define N_ROWS 8

}  // namespace TargetCalib
}  // namespace CTA
#endif  // INCLUDE_TARGETCALIB_CONSTANTS_H_
