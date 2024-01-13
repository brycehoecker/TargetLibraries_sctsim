// Copyright (c) 2015 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains DataPacket class and definitions
 * related to the T data format
 */

#ifndef INCLUDE_TARGETDRIVER_DATAPACKET_H_
#define INCLUDE_TARGETDRIVER_DATAPACKET_H_

#include <iostream>
#include <string>

#include "TargetDriver/Waveform.h"

//  #define PERFORM_CRC_CHECK
// clang-format off
#define T_PACKET_HEADER_WORDS         8
#define T_PACKET_FOOTER_WORDS         2
#define T_WAVEFORM_HEADER_WORDS       1
#define T_SAMPLES_PER_WAVEFORM_BLOCK 32
// clang-format on

// clang-format off
#define T_PACKET_OK                0
#define T_PACKET_ERROR_NODATA      1
#define T_PACKET_ERROR_BADLENGTH   2
#define T_PACKET_ERROR_BADCRC      3
#define T_PACKET_ERROR_LASTBYTES   4
#define T_PACKET_ERROR_NOWAVEFORMS 5
// clang-format on

namespace CTA {
namespace TargetDriver {

/*!
 * @class DataPacket
 * @brief Data packet for TARGET modules
 *
 * COMMENTS HARM:
 *
 * - We should review inline / virtual / explicit /static /const
 *
 */

class DataPacket {
 public:
  DataPacket(uint16_t waveforms_per_packet,
             uint16_t samples_per_waveform);  // for simulations
  explicit DataPacket(uint16_t packetsize = 0);
  virtual ~DataPacket() { Deallocate(); }
  bool IsEmpty() const;
  bool IsValid();
  int GetStatus() { return fStatusFlag; };
  std::string GetStatusString() { return fStatusString; };

  uint8_t GetASICID() const {
    return (fData[16] >> 5) & 0x3;
  }  // of first waveform
  uint8_t GetChannelID() const {
    return (fData[16] >> 1) & 0xF;
  }  // of first waveform
  uint16_t GetNumberOfWaveforms() const { return fData[0] & 0x7F; }
  uint16_t GetBuffers() const { return (fData[1] >> 2) & 0x3F; }
  uint16_t GetWaveformLength() const {
    return GetBuffers() / 2;
  }  // in 32 sample blocks
  uint16_t GetWaveformSamples() const { return (GetWaveformBytes() / 2); }
  uint16_t GetWaveformBytes() const {
    return (fData[1] >> 2 & 0x3F) * T_SAMPLES_PER_WAVEFORM_BLOCK;
  }

  bool IsFirstSubPacket() const {
    return fData[1] & 0x2;
  }  // need to implement for sims
  bool IsLastSubPacket() const { return fData[1] & 0x1; }
  uint16_t GetTotalSizeInBytes() const {
    return GetNumberOfWaveforms() *
               (GetBuffers() * T_SAMPLES_PER_WAVEFORM_BLOCK + 2) +
           2 * (T_PACKET_HEADER_WORDS + T_PACKET_FOOTER_WORDS);
  }
  uint16_t GetEventNumber() const {
    return static_cast<uint16_t>((uint16_t(fData[2]) << 8) | fData[3]);
  }
  ////  uint8_t  GetTelescopeID() const {return fData[4];}
  uint8_t GetSlotID() const { return fData[4]; }
  uint8_t GetDetectorID() const { return fData[5]; }

  uint8_t GetEventSequenceNumber() const { return fData[6]; }
  uint8_t GetDetectorUniqueTag() const { return fData[7]; }
  uint64_t GetTACKTime() const;
  uint8_t GetTACKMode() const { return fData[17] >> 6; }
  bool IsZeroSupressionEnabled() const { return fData[14] & 0x8; }
  uint8_t GetStaleBit() const { return  (fData[14] >> 6) & 0x1; }
  uint8_t GetColumn() const { return fData[14] & 0x3F; }
  uint8_t GetRow() const { return (fData[15] >> 5) & 0x7; }
  uint8_t GetBlockPhase() const { return fData[15] & 0x1F; }

  static uint16_t CalculateFirstCellId(uint16_t pRow, uint16_t pColumn,
                                       uint16_t pBlockPhase) {
    return ((pColumn * 8u) + pRow) * T_SAMPLES_PER_WAVEFORM_BLOCK + pBlockPhase;
  }
  /// Helper function to get packets size
  static uint16_t CalculatePacketSizeInBytes(uint16_t pWaveformsPerPacket,
                                             uint16_t pSamplesPerWaveform) {
    uint16_t nBlocks = 2 * (pSamplesPerWaveform / T_SAMPLES_PER_WAVEFORM_BLOCK);
    return pWaveformsPerPacket * (nBlocks * T_SAMPLES_PER_WAVEFORM_BLOCK + 2) +
           2 * (T_PACKET_HEADER_WORDS + T_PACKET_FOOTER_WORDS);
  }

  static void CalculateRowColumnBlockPhase(
      uint16_t pCellId, uint16_t& pRow,  // NOLINT(runtime/references)
      uint16_t& pColumn,                 // NOLINT(runtime/references)
      uint16_t& pBlockPhase) {           // NOLINT(runtime/references)
    pBlockPhase = (pCellId % T_SAMPLES_PER_WAVEFORM_BLOCK);
    pRow = (pCellId / T_SAMPLES_PER_WAVEFORM_BLOCK) % 8u;
    pColumn = (pCellId / T_SAMPLES_PER_WAVEFORM_BLOCK) / 8u;
  }

  /// Return the total number of cells per ASIC channel
  static uint16_t GetNCells() {
    return CalculateFirstCellId(7, 63, 0) + T_SAMPLES_PER_WAVEFORM_BLOCK;
  }

  uint16_t GetFirstCellId() const {
    return CalculateFirstCellId(GetRow(), GetColumn(), GetBlockPhase());
  }

  Waveform* GetWaveform(uint16_t waveformindex);
  bool GetPacketID(uint16_t& packet_id);  // NOLINT(runtime/references)
  void AssociateWaveform(uint16_t n,
                         Waveform& pWaveform);  // NOLINT(runtime/references)

  // For simulation mode - untested
  void FillHeader(uint16_t waves_per_packet, uint16_t waveform_samples,
                  uint8_t camera_slot_id, uint8_t module_index,
                  uint8_t event_sequence_number, uint64_t tack, uint8_t quad,
                  uint8_t row, uint8_t col);
  // Use PackWaveform to fill individual waveforms
  // For simulation mode - untested
  void FillFooter();

  void SummarisePacket(
      std::ostream& os = std::cout);  // NOLINT(runtime/references)

  // Functions from old DataPacket class
  void Allocate(uint16_t packetsize);
  void Assign(uint8_t* data, uint16_t packetsize);
  bool Fill(const uint8_t* data, uint16_t packetsize);
  void ClearFilledFlag() { fFilled = false; }
  void Deallocate();
  bool IsFilled() const { return fFilled; }
  uint16_t GetPacketSize() const { return fPacketSize; }
  uint8_t* GetData() { return fData; }
  void Print() const;
  void FillZero();

 protected:
  uint8_t* fData;
  uint16_t fPacketSize;

  bool fFilled;
  time_t fWhenFilled;
  std::string fStatusString;
  int fStatusFlag;

 private:
  bool fAssigned;
};

inline uint64_t DataPacket::GetTACKTime() const {
  // clang-format off
  return (uint64_t(fData[12]) << 56) | (uint64_t(fData[13]) << 48) |
         (uint64_t(fData[10]) << 40) | (uint64_t(fData[11]) << 32) |
         (uint64_t(fData[ 8]) << 24) | (uint64_t(fData[ 9]) << 16) |
         (uint64_t(fData[ 2]) <<  8) | (uint64_t(fData[ 3]));
  // clang-format on
}

inline void DataPacket::Assign(uint8_t* data, uint16_t packetsize) {
  Deallocate();
  fAssigned = true;
  fPacketSize = packetsize;
  fData = data;
}

}  // namespace TargetDriver
}  // namespace CTA

#endif  // INCLUDE_TARGETDRIVER_DATAPACKET_H_
