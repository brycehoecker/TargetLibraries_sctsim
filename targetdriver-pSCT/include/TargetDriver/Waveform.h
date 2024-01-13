// Copyright (c) 2015 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains Waveform class
 */
#ifndef INCLUDE_TARGETDRIVER_WAVEFORM_H_
#define INCLUDE_TARGETDRIVER_WAVEFORM_H_

#include <sys/types.h>
#include <iostream>
#include "TargetDriver/TargetModule.h"

namespace CTA {
namespace TargetDriver {

/*!
 * @class Waveform
 * @brief Class to hold the waveform properties / access for T5/T7 and later
 *
 * TODO:
 *
 */
class Waveform {
 private:
  uint8_t* fData;

 public:
  explicit Waveform(uint8_t* data = NULL) { AssociateData(data); }
  virtual ~Waveform() {}

  void AssociateData(uint8_t* data) { fData = data; }

  inline bool IsErrorFlagOn() const { return fData[0] & 0x1; } //bit 0
  inline uint8_t GetChannel() const { return (fData[0] >> 1) & 0xF; } // bits 1..4
  inline uint8_t GetASIC() const { return (fData[0] >> 5) & 0x3; } // bits 5..6
  inline uint16_t GetSamples() const { return 16 * (fData[1] & 0x3F); }
  inline uint16_t GetADC(uint16_t n) const {
    return static_cast<uint16_t>((uint16_t(fData[2 + 2 * n] & 0xF) << 8) | fData[3 + 2 * n]);
  }
  inline uint16_t GetADC16bit(uint16_t n) const {
    return static_cast<uint16_t>((uint16_t(fData[2 + 2 * n]) << 8) | fData[3 + 2 * n]);
  }

  uint16_t GetPixelID() { return GetASIC() * TM_PIXELS_PER_ASIC + GetChannel(); }

  // Very inefficient way to copy the ADC data into an array
  virtual void GetADCArray(uint16_t* adcarray, uint16_t n) const;
  virtual void GetADC16bitArray(uint16_t* adcarray, uint16_t n) const;

  // Function to get ADC array from the waveform.
  void brycesGetADCArray(uint16_t* adcarray, uint16_t n) const;

  // Function to get 16-bit ADC array from the waveform.
  void brycesGetADC16bitArray(uint16_t* adcarray, uint16_t n) const;

  // Used for quick diagnostics - maxsamples = 0 means use all
  // RMS version has bugs. Use StdDev version instead.
  void GetMeanAndStdDev(float& mean, float& stddev, uint16_t maxsamples = 0);
  void GetMeanAndRMS(float& mean, float& rms, uint16_t maxsamples = 0);

  // Remaining methods for use in simulation mode
  void SetHeader(uint8_t asic, uint8_t chan, uint16_t samples, bool errflag);
  void SetADC(uint16_t n, uint16_t val);
  void SetADC16bit(uint16_t n, uint16_t val);
  void PackWaveform(uint8_t asic, uint8_t chan, uint16_t samples, bool errflag, uint16_t* data = NULL);
};

}  // namespace TargetDriver
}  // namespace CTA

#endif  // INCLUDE_TARGETDRIVER_TWAVEFORM_H_
