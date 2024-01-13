/*
 * TriggerPacket.h
 *
 *  Created on: 3 Nov 2017
 *      Author: giavitto
 */

#ifndef INCLUDE_TARGETDRIVER_TRIGGERPACKET_H_
#define INCLUDE_TARGETDRIVER_TRIGGERPACKET_H_

#include <cstring>

#include "TargetDriver/GenericPacket.h"

// TODO: there's not acquisition control for the backplane (yet?)
// so BP_DAQ_PORT is set to the datadest port.
#define BP_DAQ_PORT 8300
#define BP_DATADEST_PORT 8307
#define BP_TRIGGER_PACKET_SIZE 92

namespace CTA {
namespace TargetDriver {

class TriggerPacket : public GenericPacket {

  typedef enum {
    UNDEF = 0x0,
    TACK = 0x1,
    BAD = 0xff
  } messageType_t;

public:
  TriggerPacket() { Allocate(BP_TRIGGER_PACKET_SIZE); memset(fData,0,BP_TRIGGER_PACKET_SIZE); }
  bool CheckMagicNumber() const { return (*((uint16_t*)(fData)))==0xCAFE; }
  messageType_t GetMessageType() const { return ((messageType_t)fData[2]); }
  uint8_t GetMessageBodySize() const { return fData[3]; }
  uint32_t* GetBody() const { return (uint32_t*)(fData+4); }
  uint64_t GetTACK() const { return *((uint64_t*)(fData+4)); }
  uint32_t* GetTriggerPattern() const { return (uint32_t*)(fData+12); }
  bool IsTriggerActive(int superpixel) const { return GetTriggerPattern()[superpixel/32]&(1<<(superpixel%32)); }
  uint32_t GetUCTSEventCounter() const { return *((uint32_t*)(fData+76)); }
  uint32_t GetUCTSPPSCounter() const { return *((uint32_t*)(fData+80)); }
  uint32_t GetUCTSClockCounter() const { return *((uint32_t*)(fData+84)); }
  uint16_t GetTriggerType() const { return *((uint16_t*)(fData+88)); }
  static uint16_t GetTotalSizeInBytes() { return BP_TRIGGER_PACKET_SIZE; }
  void Print() const;
};

} /* namespace TargetDriver */
} /* namespace CTA */

#endif /* INCLUDE_TARGETDRIVER_TRIGGERPACKET_H_ */
