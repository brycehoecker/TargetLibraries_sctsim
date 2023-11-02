// Copyright (c) 2017 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains an Genericion for DataPacket class and
 * TargetDataPacket classes
 */

#ifndef INCLUDE_TARGETDRIVER_GENERICPACKET_H_
#define INCLUDE_TARGETDRIVER_GENERICPACKET_H_

#include <stdint.h>
#include <iostream>
#include <string>
#include <time.h>

namespace CTA {
namespace TargetDriver {

#define CHEC_UDP_MAXIMUM_PACKET_SIZE 9000

class GenericPacket {
public:
  GenericPacket();
  virtual ~GenericPacket() {};

  uint8_t* GetData() { return fData; }
  uint16_t GetPacketSize() const { return fPacketSize; }
  void SetPacketSize(uint16_t size) { fPacketSize = size; }
  // Functions from old DataPacket class
  void Allocate(uint16_t packetsize);
  void Deallocate();
  void Assign(uint8_t* data, uint16_t packetsize);
  bool Fill(const uint8_t* data, uint16_t packetsize);
  void ClearFilledFlag() { fFilled = false; }
  bool IsFilled() const { return fFilled; }
  void Print() const;
  void FillZero();

protected:
  uint8_t* fData;
  uint16_t fPacketSize; // TODO: Why on earth is this 16 bits?

  bool fFilled;
  time_t fWhenFilled;
  std::string fStatusString;
  int fStatusFlag;

private:
  bool fAssigned;


};

} // namespace TargetDriver
} // namespace CTA

#endif /* INCLUDE_TARGETDRIVER_GENERICPACKET_H_ */
