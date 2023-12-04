%module target_driver
#pragma SWIG nowarn=362,389,503

%feature("autodoc", "1");

%{
#define SWIG_FILE_WITH_INIT
#include "TargetDriver/UDPBase.h"
#include "TargetDriver/UDPClient.h"
#include "TargetDriver/UDPServer.h"
#include "TargetDriver/TargetModule.h"
#include "TargetDriver/RegisterSettings.h"
#include "TargetDriver/ModuleSimulator.h"
#include "TargetDriver/Waveform.h"
#include "TargetDriver/DataPacket.h"
#include "TargetDriver/TesterBoard.h"
#include "TargetDriver/EventHeader.h"
#include "TargetDriver/RawEvent.h"
#include "TargetDriver/EventBuffer.h"
#include "TargetDriver/DataListener.h"
#include "TargetDriver/utils.h"
using namespace CTA::TargetDriver;
%}

%include "numpy.i"
%init %{
    import_array();
%}
%apply (unsigned short* ARGOUT_ARRAY1, int DIM1) {(uint16_t* adcarray, uint16_t n)}

%include "std_list.i"
%include "std_string.i"
%include "stdint.i"
%include "typemaps.i"

// for UDPClient::SendAndReceive
%typemap(in) const void* = char*; // Give a void* input the same rules as a char* (for the const void* message argument)
%apply size_t& OUTPUT { ssize_t& resplength }; // Setup the passing of this value by reference. Passing by reference doesn't really exist for Python, so its returned instead
%typemap(in, numinputs=0) void* response (void* temp) {
  $1 = &temp;
} // Ignore the void* r argument, so the user does not need to set it from the Python side, SWIG creates the void* temp pointer itself
%typemap(argout) void* response {
  $result = PyString_FromString(static_cast<const char*>($1));
} // cast the void* resulting from the function into a char*, and then transform it into a Python string object, and add it to the return arguments

// for TargetModule::ReadRegister
%apply uint32_t &OUTPUT { uint32_t& data };
// for TargetModule::ReadSetting
%apply uint32_t &OUTPUT { uint32_t& val };
// for DataPacket::GetPacketID
%apply uint16_t &OUTPUT { uint16_t& packet_id };
// for ReadHVCurrentInput / ReadHVVoltageInput
%apply float &OUTPUT { float& val };
// for TargetModule::ReadPowerBoardID
%apply uint64_t &OUTPUT { uint64_t& val };
// for TargetModule::ReadHVDAC(uint8_t superPixel,uint8_t& val)
// should also work for read EEPROM
%apply uint8_t &OUTPUT {uint8_t& val};
// for Target module WhichHVEnabled
%apply bool &OUTPUT {bool& enabled};
// for GetFirmwareVersion(uint32_t& fw_version)
%apply uint32_t &OUTPUT { uint32_t& fw_version};
// for GetPrimaryBoardID(uint64_t& pbid)
%apply uint64_t &OUTPUT { uint64_t& pbid};


%include "TargetDriver/UDPBase.h"
%include "TargetDriver/UDPClient.h"
%include "TargetDriver/UDPServer.h"
%include "TargetDriver/TargetModule.h"
%include "TargetDriver/RegisterSettings.h"
%include "TargetDriver/ModuleSimulator.h"
%include "TargetDriver/Waveform.h"
%include "TargetDriver/DataPacket.h"
%include "TargetDriver/TesterBoard.h"
%include "TargetDriver/EventHeader.h"
%include "TargetDriver/RawEvent.h"
%include "TargetDriver/EventBuffer.h"
%include "TargetDriver/DataListener.h"
%include "TargetDriver/utils.h"