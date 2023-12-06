// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#ifndef INCLUDE_TARGETDRIVER_EVENTHEADER_H_
#define INCLUDE_TARGETDRIVER_EVENTHEADER_H_

#include <sys/time.h>
#include <string>
#include <vector>

namespace CTA {
	namespace TargetDriver {

		/*!
		@class EventHeader
		@brief
		*/
		class EventHeader {
			private:
				// Don't forget to update RawEvent::FillPacket and EventFileWriter::AddEvent,
				// if you add any new information here
				uint32_t fEventID;
				uint64_t fTACK;
				uint16_t fNPacketsFilled;
				int64_t fTimeStampSec;      //!< (sec) part of the event time stamp
				int64_t fTimeStampNonoSec;  //!< (ns) part of the event time stamp
				// TODO(Akira): Add bit flags to indicate which packets were received.

			public:
				EventHeader() : fEventID(0), fTACK(0), fNPacketsFilled(0), fTimeStampSec(0), fTimeStampNonoSec(0) {}
				virtual ~EventHeader() {}
				inline void Init() {
					SetEventID(0);
					SetTACK(0);
					SetNPacketsFilled(0);
					SetTimeStamp(0, 0);
				}

				inline void SetEventID(uint32_t pEventID) { fEventID = pEventID; }
				inline uint32_t GetEventID() const { return fEventID; }
				inline void SetTACK(uint64_t pTACK) { fTACK = pTACK; }
				inline uint64_t GetTACK() const { return fTACK; }
				inline void SetNPacketsFilled(uint16_t pNPacketsFilled) { fNPacketsFilled = pNPacketsFilled; }
				inline uint16_t GetNPacketsFilled() const { return fNPacketsFilled; }
				inline void IncrementNPacketsFilled() { ++fNPacketsFilled; }
				inline void SetTimeStamp(int64_t pSec, int64_t pNanosec) {fTimeStampSec = pSec;	fTimeStampNonoSec = pNanosec;}
				inline void GetTimeStamp(int64_t& pSec, int64_t& pNanosec) const {pSec = fTimeStampSec; pNanosec = fTimeStampNonoSec;}
				void SetTimeStampNow();
				double CalcDeltaTSinceTimeStamp() const;
				bool IfTimeStampIsZero() const { return fTimeStampSec == 0 && fTimeStampNonoSec == 0; }

				static const std::vector<std::string> kColumnType;
				static const std::vector<std::string> kColumnForm;
				static const std::vector<std::string> kColumnUnit;
		};//class EventHeader

		/// @brief Set fTimeStamp to the current system time
		inline void EventHeader::SetTimeStampNow() {
				#ifdef __MACH__
				timeval tv;
				gettimeofday(&tv, 0);
				fTimeStampSec = tv.tv_sec;
				fTimeStampNonoSec = tv.tv_usec * 1000;
				#else
				timespec ts;
				clock_gettime(CLOCK_REALTIME, &ts);
				fTimeStampSec = ts.tv_sec;
				fTimeStampNonoSec = ts.tv_nsec;
				#endif
			}//inline void EventHeader::SetTimeStampNow(

			/// @brief Calculate delta T
		inline double EventHeader::CalcDeltaTSinceTimeStamp() const {
			#ifdef __MACH__
			timeval tv;
			gettimeofday(&tv, 0);
			return tv.tv_sec - fTimeStampSec + 1e-6 * tv.tv_usec - 1e-9 * fTimeStampNonoSec;
			#else
			timespec ts;
			clock_gettime(CLOCK_REALTIME, &ts);
			return static_cast<double>(ts.tv_sec - fTimeStampSec) + 1e-9 * static_cast<double>(ts.tv_nsec - fTimeStampNonoSec);
			#endif
		}//inline double EventHeader::CalcDeltaTSinceTimeStamp
	}  // namespace TargetDriver
}  // namespace CTA

#endif  // INCLUDE_TARGETDRIVER_EVENTHEADER_H_
