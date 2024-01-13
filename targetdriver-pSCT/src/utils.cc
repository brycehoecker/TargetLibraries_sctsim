#include "TargetDriver/utils.h"
// #include <fstream>
// #include <cstdint>
// #include <filesystem>

namespace CTA {
	namespace TargetDriver {

		// namespace fs = std::filesystem;
		std::string get_default_config_dir(){
			// Until we have c++14 or c++17 we can't include <filesystem> and use fs::exists
			// if(fs::exists(TARGET_INSTALL_PATH))
			return TARGET_INSTALL_PATH +std::string("/share/TargetDriver/config/");	// Return the install path

			// This line is never reached due to the return statement above -Bryce Hoecker
			return TARGET_BUILD_PATH +std::string("/share/TargetDriver/config/");	// Return the build path
		}//std::string get_default_config_dir

		int send_waveform_packet(CTA::TargetDriver::DataPacket &p,CTA::TargetDriver::ModuleSimulator &sim, uint16_t waves,uint16_t samples){
			uint16_t* data = 0;											// Initialize a pointer to uint16_t as null
			for (uint8_t i = 0; i < waves; ++i) {						// Loop over the number of waves
				CTA::TargetDriver::Waveform* w = p.GetWaveform(i);		// Get the i-th waveform from the data packet
				w->PackWaveform(2, i, samples, false, data);			// Pack the waveform with given parameters
			}
			// Send the packet
			return sim.SendDataPacket(p.GetData(), p.GetPacketSize());	// Send the data packet and return the result
		}//int send_waveform_packet
	}//namespace TargetDriver
}//namespace CTA
