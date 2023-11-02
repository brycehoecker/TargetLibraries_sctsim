// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include <time.h>

//#include <cstring>
#include <string.h>
#include <iostream>
#include <sstream>

#include "TargetDriver/GenericPacket.h"

namespace CTA {
namespace TargetDriver {

GenericPacket::GenericPacket()
    : fData(0)
    , fPacketSize(0)
    , fFilled(false)
    , fWhenFilled(0)
    , fStatusString("")
    , fStatusFlag(0)
    , fAssigned(false)
{}

//// More general functions moved from old GenericPacket base class

void GenericPacket::Allocate(uint16_t packetsize) {
  Deallocate();
  fData = new uint8_t[packetsize];
  fPacketSize = packetsize;
}

void GenericPacket::Deallocate() {
  if (fData && !fAssigned) {
    delete[] fData;
  }
  fData = 0;
  fPacketSize = 0;
}

bool GenericPacket::Fill(const uint8_t* data, uint16_t packetsize) {
  if (packetsize != fPacketSize) {
    std::cout << "GenericPacket::Fill  - Unexpected packet size " << std::endl;
    memset(fData, 0, fPacketSize);  // needed to avoid confusion with previous packets
    return false;
  }
  if (fFilled) {
    std::cout << "GenericPacket::Fill Packet already filled " << std::endl;
    return false;
  }
  
 //std::cout << "DPF> " << (long)fData << " " << (long)data << std::endl;

  memcpy(fData, data, packetsize);

  fFilled = true;
  time(&fWhenFilled);

  return true;
}

void GenericPacket::Print() const {
  for (uint16_t i = 0; i < fPacketSize / 2; ++i) {
    printf("%4d: 0x%02X%02X ", i, fData[i * 2], fData[i * 2 + 1]);
    for (int j = 7; j >= 0; j--) {
      printf("%d", (fData[i * 2] >> j) & 0x1);
    }  // j
    printf("|");
    for (int j = 7; j >= 0; j--) {
      printf("%d", (fData[i * 2 + 1] >> j) & 0x1);
    }  // j
    printf("\n");
  }  // i
}

void GenericPacket::FillZero() {
  memset(fData, 0, fPacketSize);
}

void GenericPacket::Assign(uint8_t* data, uint16_t packetsize) {
  Deallocate();
  fAssigned = true;
  fPacketSize = packetsize;
  fData = data;
}

}  // namespace TargetDriver
}  // namespace CTA
