// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include <time.h>

//#include <cstring>
#include <string.h>
#include <iostream>
#include <sstream>

#include "TargetDriver/DataPacket.h"
#include "TargetDriver/Waveform.h"

namespace CTA {
	namespace TargetDriver {
		
		DataPacket::DataPacket(uint16_t packetsize)	: fData(0), fPacketSize(0), fFilled(false), fAssigned(false) {
			if (packetsize > 0) {
				Allocate(packetsize);
			}//if
		}//DataPacket::DataPacket

		DataPacket::DataPacket(uint16_t waveforms_per_packet, uint16_t samples_per_waveform): fData(0), fFilled(false), fAssigned(false) {
			uint16_t nblocks = 2 * (samples_per_waveform / T_SAMPLES_PER_WAVEFORM_BLOCK);
			uint16_t packetsize = waveforms_per_packet * (nblocks * T_SAMPLES_PER_WAVEFORM_BLOCK + 2) +	2 * (T_PACKET_HEADER_WORDS + T_PACKET_FOOTER_WORDS);
			Allocate(packetsize);
		}//DataPacket::DataPacket

		// TBD - IN SIMULATOR - keep internal clock and generate 'real' TACK - add Sync
		// command functionality - use register values for det/slot ID
		void DataPacket::FillHeader(uint16_t waves_per_packet, uint16_t waveform_samples, uint8_t camera_slot_id, uint8_t module_index, uint8_t event_sequence_number, uint64_t tack, uint8_t quad, uint8_t row, uint8_t col) {
			fData[0] = (waves_per_packet & 0x7F);
			uint16_t buffers = 2 * (waveform_samples / T_SAMPLES_PER_WAVEFORM_BLOCK);

			//  std::cout << "filling buffers: " << buffers << std::endl;

			fData[1] = ((buffers << 2) & 0x3F) + 1;
			fData[2] = static_cast<uint8_t>((tack >> 8) & 0xFF);
			fData[3] = static_cast<uint8_t>(tack & 0xFF);
			fData[4] = camera_slot_id;
			fData[5] = module_index;
			fData[6] = event_sequence_number;
			// TODO(Harm) - work out what the detector unique identify is/should be
			// TODO(Harm) Don't use the same parameter for two places
			fData[7] = camera_slot_id;
			fData[8] = static_cast<uint8_t>((tack >> 24) & 0xFF);
			fData[9] = static_cast<uint8_t>((tack >> 16) & 0xFF);
			fData[10] = static_cast<uint8_t>((tack >> 40) & 0xFF);
			fData[11] = static_cast<uint8_t>((tack >> 32) & 0xFF);
			fData[12] = static_cast<uint8_t>((tack >> 56) & 0xFF);
			fData[13] = static_cast<uint8_t>((tack >> 48) & 0xFF);
			// TODO(Akira) Check the row, col format again
			fData[14] = (col & 0x3F);
			fData[15] = static_cast<uint8_t>(row << 5) | (quad & 0x1F);
		}//void DataPacket::FillHeader
		
		void DataPacket::FillFooter() {
			fData[fPacketSize - 1] = 0;
			fData[fPacketSize - 2] = 0;
			fData[fPacketSize - 3] = 0;
			fData[fPacketSize - 4] = 0;
		}//void DataPacket::FillFooter

		bool DataPacket::IsEmpty() const {
			for (uint16_t i = 0; i < fPacketSize; ++i) {
				if (fData[i] != 0) {
					return false;
				}//if
			}//for
			return true;
		}//bool DataPacket::IsEmpty

		bool DataPacket::IsValid() /* const*/ {
			fStatusFlag = T_PACKET_OK;
			if (fPacketSize == 0) {
				fStatusString = "IsValid() Data length is zero";
				fStatusFlag = T_PACKET_ERROR_NODATA;
				return false;
			}//if

			uint16_t wavewords = GetWaveformSamples() + T_WAVEFORM_HEADER_WORDS;
			uint16_t packetLength = 2 * (T_PACKET_HEADER_WORDS + T_PACKET_FOOTER_WORDS + GetNumberOfWaveforms() * wavewords);
			if (packetLength != fPacketSize) {
				std::ostringstream str;
				str << "IsValid() Data length is inconsistent with the header. Calculated: "
				<< packetLength << " Actual: " << fPacketSize
				<< " WaveformBytes: " << GetWaveformBytes()
				<< " Waveforms: " << GetNumberOfWaveforms();
				fStatusString = str.str();
				fStatusFlag = T_PACKET_ERROR_BADLENGTH;
				// std::cout << GetWaveformSamples() << " " << GetBuffers() << " " << GetNumberOfWaveforms() << std::endl;
				return false;
			}//if

			#ifdef PERFORM_CRC_CHECK
			uint16_t crc = (uint16_t(fData[fPacketSize - 4]) << 8) | fData[fPacketSize - 3];
			if (crc != Util::CRC(fPacketSize - 4, fData)) {
				fStatusString = "IsValid() CRC is inconsistent with the data.";
				fStatusFlag = T_PACKET_ERROR_BADCRC;
				return false;
			}//if
			#endif

			if ((uint16_t(fData[fPacketSize - 2]) << 6) || ((fData[fPacketSize - 1] >> 2) != 0)) {
			//if ((uint16_t(fData[fPacketSize - 2]) << 6)||(fData[fPacketSize - 1] >> 2)) != 0)) {
				fStatusString = "IsValid() Problem - 14 bits of the last two bytes must be zero.";
				fStatusFlag = T_PACKET_ERROR_LASTBYTES;
				return false;
			}//if
			return true;
		}//bool DataPacket::IsValid

		Waveform* DataPacket::GetWaveform(uint16_t waveformindex) {
			Waveform* waveform = new Waveform();
			AssociateWaveform(waveformindex, *waveform);
			return waveform;
		}//Waveform* DataPacket::GetWaveform

		void DataPacket::AssociateWaveform(uint16_t waveformindex, Waveform& pWaveform) {
			uint16_t len = GetWaveformBytes();  // just the samples
			uint16_t index = 2 * T_PACKET_HEADER_WORDS + waveformindex * (len + 2 * T_WAVEFORM_HEADER_WORDS);
			pWaveform.AssociateData(&fData[index]);
		}//void DataPacket::AssociateWaveform

		bool DataPacket::GetPacketID(uint16_t& packet_id) {
			if (!IsValid()) return false;
			uint16_t nwaveforms = GetNumberOfWaveforms();
			if (nwaveforms == 0) {
				fStatusFlag = T_PACKET_ERROR_NOWAVEFORMS;
				return false;
			}
			Waveform* w = GetWaveform(0);
			uint8_t asic = w->GetASIC();
			uint8_t chan = w->GetChannel();
			uint8_t module = GetDetectorID();
			packet_id = (module * 64 + asic * 16 + chan) / nwaveforms;
			delete w;
			return true;
		}//bool DataPacket::GetPacketID

		void DataPacket::SummarisePacket(std::ostream& os) {
			Waveform* w = GetWaveform(0);
			uint16_t pid;
			GetPacketID(pid);
			os << "DataPacket id: " << pid << " det/slot " << static_cast<int>(GetDetectorID()) << "/" << static_cast<int>(GetSlotID()) 
			<< " tack: " << GetTACKTime() << " val: " << IsValid() << " waves: " << GetNumberOfWaveforms() << " samp: " << GetWaveformSamples()
			<< " row/col: " << static_cast<int>(GetRow()) << "/" << static_cast<int>(GetColumn()) 
			<< " ADC vals: " << w->GetADC(2) << " "	<< w->GetADC(3) << " " << w->GetADC(4) << " " << w->GetADC(5) << std::endl;

			delete w;
		}//void DataPacket::SummarisePacket

		//// More general functions moved from old DataPacket base class

		void DataPacket::Allocate(uint16_t packetsize) {
			Deallocate();
			fData = new uint8_t[packetsize];			//HERE IS A NEW COMMAND CHECK HERE IF THERE ARE MEMORY LEAKS
			fPacketSize = packetsize;
		}//void DataPacket::Allocate

		void DataPacket::Deallocate() {
			if (fData && !fAssigned) {
				delete[] fData;
			}//if
			fData = 0;
			fPacketSize = 0;
		}//void DataPacket::Deallocate

		bool DataPacket::Fill(const uint8_t* data, uint16_t packetsize) {
			if (packetsize != fPacketSize) {
				std::cout << "DataPacket::Fill  - Unexpected packet size " << std::endl;
				memset(fData, 0,
				fPacketSize);  // needed to avoid confusion with previous packets
				return false;
			}//if (packetsize != fPacketSize)
			if (fFilled) {
				std::cout << "DataPacket::Fill Packet already filled " << std::endl;
				return false;
			}//if (fFilled) 
			
			// std::cout << "DPF> " << (long)fData << " " << (long)data << std::endl;
			
			memcpy(fData, data, packetsize);
			fFilled = true;
			time(&fWhenFilled);
			return true;
		}//bool DataPacket::Fill

		void DataPacket::Print() const {
			for (uint16_t i = 0; i < fPacketSize / 2; ++i) {
				printf("%4d: 0x%02X%02X ", i, fData[i * 2], fData[i * 2 + 1]);
				for (int j = 7; j >= 0; j--) {
					printf("%d", (fData[i * 2] >> j) & 0x1);
				}//for (int j = 7...
				printf("|");
				for (int j = 7; j >= 0; j--) {
					printf("%d", (fData[i * 2 + 1] >> j) & 0x1);
				}//for (int j = 7...
				printf("\n");
			}//for (uint16_t i = 0
		}//void DataPacket::Print

		void DataPacket::FillZero() { memset(fData, 0, fPacketSize); }

	}  // namespace TargetDriver
}  // namespace CTA
