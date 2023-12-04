// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#ifndef INCLUDE_TARGETDRIVER_UTILS_H_
#define INCLUDE_TARGETDRIVER_UTILS_H_


#include <string>

#include "TargetDriver/ModuleSimulator.h"
#include "TargetDriver/DataPacket.h"

namespace CTA {
namespace TargetDriver {

std::string get_default_config_dir();

int send_waveform_packet(CTA::TargetDriver::DataPacket &p,CTA::TargetDriver::ModuleSimulator &sim, uint16_t waves,uint16_t samples);

}
}
#endif