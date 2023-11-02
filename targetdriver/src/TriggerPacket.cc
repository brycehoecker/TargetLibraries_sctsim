/*
 * TriggerPacket.cc
 *
 *  Created on: 3 Nov 2017
 *      Author: giavitto
 */

#include "TargetDriver/TriggerPacket.h"

namespace CTA {
namespace TargetDriver {

  void TriggerPacket::Print() const {
    GenericPacket::Print();
    std::cout << "Trigger Packet" << std::endl;
    std::cout << std::hex << "Magic Number: \t\t0x" << (*((uint16_t*)(fData))) << std::endl;
    std::cout << std::dec << "Message Type: \t\t" << GetMessageType() << std::endl;
    std::cout << std::dec << "Message Body Size: \t\t" << GetMessageBodySize() << std::endl;
    std::cout << std::hex << "TACK: \t\t0x" << GetTACK() << std::endl;
    std::cout << std::dec << "Trigger Pattern: \t\t";
    for (int i=0; i<512; ++i) { std::cout << IsTriggerActive(i); }
    std::cout << std::endl;
    std::cout << std::hex << "UCTS Event Counter: \t\t" << GetUCTSEventCounter() << std::endl;
    std::cout << std::hex << "UCTS PPS Counter: \t\t" << GetUCTSPPSCounter() << std::endl;
    std::cout << std::hex << "UCTS Clock Counter: \t\t" << GetUCTSClockCounter() << std::endl;
    std::cout << std::hex << "Trigger Type: \t\t" << GetTriggerType() << std::endl;

  }
} /* namespace TargetDriver */
} /* namespace CTA */
