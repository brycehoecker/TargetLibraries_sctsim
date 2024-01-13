// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include "TargetDriver/RawEvent.h"

namespace CTA {
	namespace TargetDriver {

		double RawEvent::fTimeoutSec = 0.3;

		RawEvent::RawEvent(uint16_t pNPacketsPerEvent, uint16_t pPacketSize) : fTimedOut(false) {
			Clear();
			// fDataPackets.resize(pNPacketsPerEvent);
			// for (auto it = fDataPackets.begin(); it != fDataPackets.end(); ++it) {
			//   *it = std::make_shared<CTA::TargetDriver::DataPacket>(pPacketSize);
			// }
			fDataPackets.reserve(pNPacketsPerEvent);
			for (uint32_t i = 0; i < pNPacketsPerEvent; ++i) {
				fDataPackets.push_back(new DataPacket(pPacketSize));
			}//for
		}//RawEvent::RawEvent

		/// Initialize the internal states and clear data packets' flag.
		void RawEvent::Clear() {
			fEventHeader.Init();
			fTimedOut = false;
			fFlushed = false;
			fRead = false;
			fWaveformCheckStatus = true;
			for (auto it = fDataPackets.begin(); it != fDataPackets.end(); ++it) {
				(*it)->ClearFilledFlag();
			}//for
		}//void RawEvent::Clear

		/// Add a new data packet (uint8_t array) to the packet vector. The data is
		/// memcopied to the vector.
		bool RawEvent::AddNewPacket(const uint8_t* data, uint16_t packetID,	uint16_t packetSize, bool checkflag) {
			if (packetID >= fDataPackets.size()) {
				std::cerr << "Bad Packet ID: " << packetID;
				return false;
			}//if

			DataPacket* packet = fDataPackets[packetID];
			// TODO(Akira): check for overwrite?

			bool filled = packet->Fill(data, packetSize);
			/// bool filled = true;

			if (filled) {
				fEventHeader.IncrementNPacketsFilled();
				if (fEventHeader.GetNPacketsFilled() == 1) {
					// Is this really OK to write the time stamp at this point?
					// usec order delay is expected after the actual arrival time of the first
					// packet
					fEventHeader.SetTimeStampNow();
					fEventHeader.SetTACK(packet->GetTACKTime());
				}
				if (checkflag) {
					Waveform* w = packet->GetWaveform(0);
					float rms, mean;
					w->GetMeanAndRMS(mean, rms, 10);
					///      std::cout << "Check: " << mean << " " << rms << std::endl;
					fWaveformCheckStatus = ((mean < 900.0) && (rms < 100.0));
					//TODO(Bryce): check if below is running correctly (cerr isn't "IN" the if statement)
					if (!fWaveformCheckStatus)
					std::cerr << "RawEvent::FillPacket - Suspicious waveform - mean " << mean << " rms " << rms << std::endl;
				}
			} else {
				std::cerr << "RawEvent::FillPacket - failed to fill packet ID: " << packetID 
				<< " size was " << packetSize << " expected " << packet->GetPacketSize() << " - event ID " << fEventHeader.GetEventID();
			}

			return filled;
		}//bool RawEvent::AddNewPacket
	}// namespace TargetDriver
}// namespace CTA
