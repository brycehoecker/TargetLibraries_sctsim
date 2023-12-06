#include <ostream>

#include "TargetDriver/EventBuffer.h"

namespace CTA {
	namespace TargetDriver {

		//----------------------------------------------------------------------
		EventBuffer::EventBuffer(uint32_t pBufferDepth, uint16_t pNPacketsPerEvent,
								uint16_t pPacketSize, float pBuildTimeout, uint32_t pCheckFreq) {
									
			float bufferGbs = 1e-9f * pBufferDepth * pNPacketsPerEvent * pPacketSize;
			std::cout << "Allocating " << bufferGbs << " GB for EventBuffer" << std::endl;

			fEventVector.resize(pBufferDepth);
			for (auto it = fEventVector.begin(); it != fEventVector.end(); ++it) {
				(*it) = new RawEvent(pNPacketsPerEvent, pPacketSize);
				(*it)->SetTimeoutSec(pBuildTimeout);
			}//for
			fPacketsArrivedByPID.resize(pNPacketsPerEvent, 0);
			Clear();
			fCheckFreq = pCheckFreq;
		}//EventBuffer::EventBuffer
		//----------------------------------------------------------------------
		void EventBuffer::DiagnosticReport(std::ostream& stream) const {
			stream << "index \t evid \t is_being_built \t complete \t was_read \t is_empty" << std::endl;

			buffer_it it = fBufferBegin;
			int i=0;
			while (it != fBufferEnd) {
				auto ev = *it;
				stream << i << "\t" << ev->GetEventHeader().GetEventID() << "\t" << ev->IsBeingBuilt() << "\t" << ev->IsComplete() << "\t" << ev->WasRead() << "\t" << ev->IsEmpty() << std::endl;
				++it;
				++i;
			}//while
		}//void EventBuffer::DiagnosticReport(std::ostream& stream) const 
		//----------------------------------------------------------------------
		int64_t EventBuffer::GetNumberIncomplete() const {
			int64_t fin = GetFinishedIndex();
			int64_t wr = GetWriteIndex();
			int64_t n = wr-fin;
			if (n<0) n += fEventVector.size();
			return n;
		}//int64_t EventBuffer::GetNumberIncomplete() const 
		//----------------------------------------------------------------------
		int64_t EventBuffer::GetNumberToBeRead() const {
			int64_t fin = GetFinishedIndex();
			int64_t rd = GetReadIndex();
			int64_t n = rd-fin;
			if (n<0) n += fEventVector.size();
			return n;
		}//int64_t EventBuffer::GetNumberToBeRead() const 

		//----------------------------------------------------------------------
		// TEST NEW APPROACH
		//  Later: pPacketID = -1 --> the trigger packet
		#ifdef NEWEVBUILDING
		bool EventBuffer::AddNewPacket(const uint8_t* pData, uint32_t pEventID,
										uint16_t pPacketID, uint16_t pPacketSize) {
										//int pPacketID, uint16_t pPacketSize) {
			/// 0) Deal with packets arriving after a flush
			static bool flashErrorMessageWasPrinted = false;
			if (fFlushed) {
				if (!flashErrorMessageWasPrinted) {
					std::cerr << "Packet arrived after Flush() - ignoring packet "
					<< pPacketID << " of event " << pEventID
					<< " and all packets later\n";
					flashErrorMessageWasPrinted = true;
				}//if (!flashErrorMessageWasPrinted)
				return false;
			}//if (fFlushed)

			// 1) Count packets
			// bool trig = (pPacketID == TRIG_PACKET); // -1
			// if (trig) {
			//   ++fTriggerPacketsArrived;
			// } else {
			++fPacketsArrived;
			if (pPacketID < fPacketsArrivedByPID.size()) {
				++fPacketsArrivedByPID[pPacketID];
			} else {
				std::cerr << "Unexpected packet ID arrived at buffer" << std::endl;
				return false;
			}
			//}
			// Check every now and again if waveforms look crazy
			bool checkflag = ((fCheckFreq>0) && (fPacketsArrived % fCheckFreq == 0));

			//  std::cout << "J: Arrived " << pPacketID << " " << pEventID << std::endl;
			// 2) Find the buffer index of this event

			buffer_it it = fBufferBegin;
			bool found = false;
			// Start by checking if this packet fits in the event at the head of the buffer or is the first packet to go in to the buffer
			if (fWriteIterator != fWriteIteratorNotInitialized) {
				uint32_t evid = (*fWriteIterator)->GetEventHeader().GetEventID(); // if there is any overhead here could keep a separate list of IDs
				if (evid == pEventID) {
					found = true;
					it = fWriteIterator;
				} else {
					// a) start with the first event that is not complete
					it = fFinishedIterator == fNoFinishedEvents
					? fBufferBegin : fFinishedIterator;
					if (it == fBufferEnd) it = fBufferBegin; // Wrap around

					// b) keep looking until we reach the write iterator - if we get there is this a new event
					while (!found && it != fWriteIterator) {
						auto ev = *it;
						if (ev->IsBeingBuilt()) {
							evid = ev->GetEventHeader().GetEventID(); // if there is any overhead here could keep a separate list of IDs
							if (evid == pEventID) found = true;
						} else {
							++it;
							if (it == fBufferEnd) {
								it = fBufferBegin; // Wrap around
							}
						}
						//	std::cout << "J: evid to check " << evid << " found " << found << " it dist: " << std::distance(fBufferBegin, it) << " " << ev->IsBeingBuilt() << std::endl;
					}//while
				}
			} else {
			// Point to the beginning of the buffer (was the default)
			//    std::cout << "J: point to beginning of the buffer" <<std::endl;
			}
			auto event = *it;

			/// 3) If this packet belongs to an existing event - add it
			if (found) {
				// if (event->IsBeingBuilt() && !event->WasRead()) {
				//   std::cerr << "strange case" << std::endl; // TODO: improve debugging
				// } 
				// if (trig) {
				//   event->AddNewTriggerPacket(pData, pPacketSize);
				// } else {
				//    std::cout << "J: adding packet to existing event" << std::endl;
				event->AddNewPacket(pData, pPacketID, pPacketSize, checkflag);
				//}
				if (event->IsComplete()) {  // Is this event now complete?
					//std::cout << "J: event now complete " << std::distance(fBufferBegin, fWriteIterator) << std::endl;
					fFinishedMutex.lock();
					AdvanceFinishedIterator(it);
					fFinishedMutex.unlock();
				}
			} else {
				// 4) Make a new event starting with this packet
				if (fWriteIterator == fWriteIteratorNotInitialized) {
					fWriteIterator = fBufferBegin;
				} else { 
					++fWriteIterator;
					if (fWriteIterator == fBufferEnd) {
						fWriteIterator = fBufferBegin;
					}
				}
				event = *fWriteIterator;
				if (!event->IsEmpty() && !event->WasRead()) {
					++fPacketsDropped;
					// JAH - unhelpful to print this thousands of times after buffer has filled
					if ((fPacketsDropped == 1) || (fPacketsDropped % 50000) == 0) {
						std::cerr << "Buffer full. Failed to store packet " << pPacketID << " of event " << pEventID << " - latest event ID was " 
						<< (*fWriteIterator)->GetEventHeader().GetEventID() << " - have now dropped - " << fPacketsDropped << " packets " << std::endl;
					}
					return false;
				}
				event->Clear();
				event->GetEventHeader().SetEventID(pEventID);
				// std::cout << "J: made new event " << pEventID << " at " 
				// 	      << std::distance(fBufferBegin, it) << " writeit is at " 
				// 	      << std::distance(fBufferBegin, fWriteIterator) << std::endl;
				// if (trig) {
				//   event->AddNewTriggerPacket(pData, pPacketSize);
				// } else {
				event->AddNewPacket(pData, pPacketID, pPacketSize, checkflag);
				//    std::cout << "J: write iterator now at " << std::distance(fBufferBegin, fWriteIterator) << std::endl;
			}//else

			if (checkflag) {
				++fWaveformChecks;
				if (!event->WaveformCheckStatus()) ++fFailedWaveformChecks;
			}
			//  std::cout << "---done" << std::endl;
			return true;

		}//bool EventBuffer::AddNewPacket
		#else
		//----------------------------------------------------------------------

		bool EventBuffer::AddNewPacket(const uint8_t* pData, uint32_t pEventID,
										uint16_t pPacketID, uint16_t pPacketSize) {
			static bool flashErrorMessageWasPrinted = false;
			if (fFlushed) {
				if (!flashErrorMessageWasPrinted) {
					std::cerr << "Packet arrived after Flush() - ignoring packet "
					<< pPacketID << " of event " << pEventID
					<< " and all packets later\n";
					flashErrorMessageWasPrinted = true;
				}
				return false;
			}

			//  fWriteMutex.lock(); // JAH - I don't see why we need this - and it could
			//  have performance implications

			fFinishedMutex.lock();

			// start with the first event that is not finished and try to fit in this
			// packet
			buffer_it it = fFinishedIterator == fNoFinishedEvents
			? fBufferBegin : std::next(fFinishedIterator);
			//Above line is confusing but can be explained more clearly by the line below
			//If fFinishedIterator is equal to fNoFinishedEvents (i.e., if there are no finished events), then it is set to fBufferBegin (the start of the buffer).
			
			if (it == fBufferEnd) {
				// All events up to end of buffer are finished -> wrap around
				it = fBufferBegin;
			}
			fFinishedMutex.unlock();

			++fPacketsArrived;
			if (pPacketID < fPacketsArrivedByPID.size()) {
				++fPacketsArrivedByPID[pPacketID];
			} else {
				std::cerr << "Unexpected packet ID arrived at buffer" << std::endl;
			}

			// Check every now and again if waveforms look crazy
			bool checkflag = ((fCheckFreq > 0) && (fPacketsArrived % fCheckFreq == 0));

			std::size_t n = fEventVector.size();
			for (std::size_t i = 0; i < n; ++i) {  // check all event slots in worst case
				auto event = *it;
				uint32_t evid = event->GetEventHeader().GetEventID();

				// won't check if this event was flushed or not, because fFlushed flag
				// should have been updated as well.
				if (evid == pEventID && event->IsBeingBuilt()) {
				if (!event->WasRead()) {
				event->AddNewPacket(pData, pPacketID, pPacketSize, checkflag);
				if (checkflag) {
				++fWaveformChecks;
				if (!event->WaveformCheckStatus()) ++fFailedWaveformChecks;
				}
				} else {
				std::cerr << "Event " << pEventID << " was already read - had filled "
				<< event->GetEventHeader().GetNPacketsFilled()
				<< " packets\n";
				}

				if (event->IsComplete()) {  // Is this event now complete?
				fFinishedMutex.lock();
				AdvanceFinishedIterator(it);
				fFinishedMutex.unlock();
				}

				//      fWriteMutex.unlock();
				return true;
				} else if (event->IsComplete() && !event->WasRead()) {
				fFinishedMutex.lock();
				AdvanceFinishedIterator(it);
				fFinishedMutex.unlock();
				} else {
					// This event is not being built and can start writing to it
					if ((it == (fWriteIterator == fWriteIteratorNotInitialized ? fBufferBegin : std::next(fWriteIterator))) ||
						(it == fBufferBegin && fWriteIterator == fBufferLast)) {
						// Start a new event just after the write iterator
						if (!event->IsEmpty() && !event->WasRead()) {
							// std::cerr << "About to overwrite an event (Event ID "
							//           << event->GetEventHeader().GetEventID()
							//           << ") that has not yet been read " << std::endl;
							fEventsOverwritten++;
							//	  fPause = true;
							// std::cerr << "WARNING: Buffer Filled - Flushing" << std::endl;
							// Flush(); -- doesn't work...
							//	  return false;
						}
						event->Clear();
						event->GetEventHeader().SetEventID(pEventID);
						event->AddNewPacket(pData, pPacketID, pPacketSize, checkflag);
						if (checkflag && !event->WaveformCheckStatus()) fFailedWaveformChecks++;
						// Move the write pointer
						if (fWriteIterator == fWriteIteratorNotInitialized) {
							fWriteIterator = fBufferBegin;
						} else {
							++fWriteIterator;
							if (fWriteIterator == fBufferEnd) {
								fWriteIterator = fBufferBegin;
							}
						}
						//        fWriteMutex.unlock();
						return true;
					}
				}
				++it;  // try the next event
				if (it == fBufferEnd) {
					it = fBufferBegin;
				}
			}

			// Failed to store this packet anywhere
			++fPacketsDropped;
			// JAH - unhelpful to print this thousands of times after buffer has filled
			if ((fPacketsDropped == 1) || (fPacketsDropped % 10000) == 0) {
				std::cerr << "Failed to store packet " << pPacketID << " of event "	<< pEventID << " - latest event ID was "
				<< (*fWriteIterator)->GetEventHeader().GetEventID()	<< " - have now dropped - " << fPacketsDropped << " packets " << std::endl;
			}
			//  fWriteMutex.unlock();
			return false;
		}//bool EventBuffer::AddNewPacket
		#endif
		void EventBuffer::AdvanceFinishedIterator(buffer_it pNextIterator) {
			// If this is a finished event just after the finished pointer - the finished
			// pointer can be advanced
			if (fFinishedIterator == std::prev(pNextIterator) || (fFinishedIterator == fBufferLast && pNextIterator == fBufferBegin)) {
				++fFinishedIterator;
			} else if (fFinishedIterator == fNoFinishedEvents && pNextIterator == fBufferBegin) {
				fFinishedIterator = fBufferBegin;
				return;
			} else {
				return;
			}
			if (fFinishedIterator == fBufferEnd) {
				fFinishedIterator = fBufferBegin;
			}
		}//void EventBuffer::AdvanceFinishedIterator(buffer_it pNextIterator)

		void EventBuffer::Clear() {
			ClearEvents();
			InitializeMembers();
		}

		void EventBuffer::ClearEvents() {
			for (auto it = fEventVector.begin(); it != fEventVector.end(); ++it) {
				(*it)->Clear();
			}
		}

		void EventBuffer::Flush() {
			// Give up on any incomplete events - allow everything in the buffer to be
			// read

			if (fWriteIterator == fWriteIteratorNotInitialized) {
				return;
			}

			fFinishedMutex.lock();
			//  fWriteMutex.lock();

			if (std::distance(fFinishedIterator, fWriteIterator) >= 0) {
				for (auto it = fFinishedIterator; it != std::next(fWriteIterator); ++it) {
					if ((*it)->IsBeingBuilt()) {
						(*it)->SetToFlushed();
					}
				}
			} else {
				for (auto it = fFinishedIterator; it != fBufferEnd; ++it) {
					if ((*it)->IsBeingBuilt()) {
						(*it)->SetToFlushed();
					}
				}
				for (auto it = fBufferBegin; it != std::next(fWriteIterator); ++it) {
					if ((*it)->IsBeingBuilt()) {
						(*it)->SetToFlushed();
					}
				}
			}
			fFinishedIterator = fWriteIterator;
			fFlushed = true;
			//  fWriteMutex.unlock();
			fFinishedMutex.unlock();
		}//void EventBuffer::Flush()

		void EventBuffer::InitializeMembers() {
			fBufferBegin = fEventVector.begin();
			fBufferEnd = fEventVector.end();
			fBufferLast = std::prev(fBufferEnd);

			fNoFinishedEvents = fBufferEnd;
			fWriteIteratorNotInitialized = fBufferEnd;
			fReadIterator = fBufferBegin;
			fWriteIterator = fWriteIteratorNotInitialized;
			fFinishedIterator = fNoFinishedEvents;

			fFlushed = false;

			fPacketsArrived = 0;
			fPacketsDropped = 0;
			fEventsBuilt = 0;
			fEventsRead = 0;
			fEventsTimedOut = 0;
			fEventsOverwritten = 0;
			fWaveformChecks = 0;
			fFailedWaveformChecks = 0;

			for (uint32_t i = 0; i < fPacketsArrivedByPID.size(); ++i) {
				fPacketsArrivedByPID[i] = 0;
			}
		}//void EventBuffer::InitializeMembers()

		bool EventBuffer::StatusOK() const {
			if (fEventsOverwritten > 0) {
				std::cout << "Event Buffer Status - Bad - events have been overwritten" << std::endl;
				return false;
			}
			if (fEventsRead > 1000) {
				float frac_timedout = fEventsTimedOut / (float)fEventsRead;
				if (frac_timedout > 0.2) {
					std::cout << "Event Buffer Status - Bad - too many timed out events" << std::endl;
					return false;
				}
				if (fPacketsArrived > 2000) {
					float frac_dropped = fPacketsDropped / (float)fPacketsArrived;
					if (frac_dropped > 0.2) {
						std::cout << "Event Buffer Status - Bad - too many dropped packets" << std::endl;
						return false;
					}
				}
			}

			if (fFailedWaveformChecks > 20) {
				std::cout << "Event Buffer Status - Bad - too many failed waveform checks" << std::endl;
				return false;
			}
			int buflen = std::distance(fBufferBegin, fBufferEnd);
			int incomp = GetNumberIncomplete();
			int toberead = GetNumberToBeRead();

			if (incomp > 0.25*buflen) {
				std::cout << "Event Buffer Status - Bad - incomplete events fill more than a quarter  of the buffer" << std::endl;
				return false;
			}
			if (toberead> 0.9*buflen) {
				std::cout << "Event Buffer Status - Bad - events waiting to be written to disk fill over 90% of the buffer (bufflen = " << buflen << ")" << std::endl;
				//return false;
			}
			return true;
		}//bool EventBuffer::StatusOK() const

		// std::shared_ptr<RawEvent> EventBuffer::ReadEvent() {
		RawEvent* EventBuffer::ReadEvent() {
			fFinishedMutex.lock();

			// Check if the event pointed by fReadIterator is timed out or not
			auto ev = *fReadIterator;
			if (ev->WasRead()) {
				// This event slot was filled in the previous loop of the event buffer, but
				// a new event has not been created in it yet.
				fFinishedMutex.unlock();
				return NULL;  // std::shared_ptr<RawEvent>();  // nothing to read
			} else {
				if (ev->IsBeingBuilt()) {
				if (ev->WasFlushed()) {
				std::cerr << "Event " << ev->GetEventHeader().GetEventID()
				<< " was flushed - had filled "
				<< ev->GetEventHeader().GetNPacketsFilled() << " packets.\n";
				goto ret;
			} else if (ev->IsTimedOut()) {
				// Jim - moving this from NewPacket could have performance
				// implications...
				++fEventsTimedOut;
				if (fEventsTimedOut % 1000 == 0) {
					std::cerr << "Event " << ev->GetEventHeader().GetEventID()
					<< " timed out - had filled "
					<< ev->GetEventHeader().GetNPacketsFilled()
					<< " packets - have now timed out on " << fEventsTimedOut
					<< " events \n";
				}
				AdvanceFinishedIterator(fReadIterator);
				goto ret;
				} else {
					fFinishedMutex.unlock();
					return NULL;  // std::shared_ptr<RawEvent>();  // nothing to read
					}
				} else if (ev->IsComplete()) {
					++fEventsBuilt;
					AdvanceFinishedIterator(fReadIterator);
					goto ret;
				} else {
					fFinishedMutex.unlock();
					return NULL;  // std::shared_ptr<RawEvent>();  // nothing to read
				}
			}

			ret:
			//TODO: (Bryce) Remove the dang gotos 
			// This event should have not been read yet, because fReadIterator is always
			// incremented after an event is read
			ev->SetToRead();

			++fReadIterator;
			if (fReadIterator == fBufferEnd) {
				fReadIterator = fBufferBegin;
			}
			++fEventsRead;
			fFinishedMutex.unlock();

			return ev;
		}//RawEvent* EventBuffer::ReadEvent()

		float EventBuffer::GetEventRate() const {
			if ((fWriteIterator == fWriteIteratorNotInitialized) ||	(fFinishedIterator == fNoFinishedEvents)) return 0.0;
			std::cout << "GetEventRate()" << std::endl;

			auto evNow = *fFinishedIterator;
			auto evOld = *(std::next(fWriteIterator));

			int evs = 0;
			float dt_sec = 1.0;
			int buflen = std::distance(fBufferBegin, fBufferEnd);
			int incomp = GetNumberIncomplete();

			uint64_t tackNow = evNow->GetEventHeader().GetTACK();
			uint64_t tackOld = evOld->GetEventHeader().GetTACK();

			double time_since = evNow->GetEventHeader().CalcDeltaTSinceTimeStamp();
			if (time_since>1.0) {
				std::cout << "No new events for " << time_since << " seconds. Finished iterator: " << std::distance(fBufferBegin, fFinishedIterator) 
				<< " write iterator: " << std::distance(fBufferBegin, fWriteIterator) << " incomplete: " << incomp << " to be read: " << GetNumberToBeRead() << std::endl;
				return 0.0;
			}
			if (tackOld > 0) {
				if (tackOld > tackNow) {
					std::cout << "TACK problem in GetEventRate (A) " << tackOld << " " << tackNow << std::endl;
				}
				evs = buflen - incomp - 1;
			} else {
				evOld = *fBufferBegin;
				tackOld = evOld->GetEventHeader().GetTACK();
				if (tackOld > tackNow) {
					std::cout << "TACK problem in GetEventRate (B) " << tackOld << " " << tackNow << std::endl;
				}
				evs = std::distance(fBufferBegin, fFinishedIterator);
			}
			dt_sec = (tackNow - tackOld) * 1.0e-9f;

			float rate = 0;
			if (dt_sec > 0) 
			rate = evs/dt_sec;
			
			std::cout << std::dec << "Rate: " << rate << " Hz (from last " << evs << " events), Buffer Status: length "	
			<< buflen << " incomplete: " <<	incomp << " to be read: " << GetNumberToBeRead() << std::endl;
			
			std::cout << "GetEventRate() done" << std::endl;
			return rate;
		}//float EventBuffer::GetEventRate() const 

		void EventBuffer::Report(std::ostream& stream) const {
			stream << "EventBuffer::Report | Packets received: " << fPacketsArrived
			<< " and dropped: " << fPacketsDropped << " - Events built "
			<< fEventsBuilt << " timed out " << fEventsTimedOut << " read "
			<< fEventsRead << " overwritten " << fEventsOverwritten << "\t";

			stream << "Number of packets that have arrived - by packet ID: ";
			for (unsigned int i = 0; i < fPacketsArrivedByPID.size(); ++i) {
				if ((i % 8) == 0) stream << "\t" << i << " to " << i + 7 << " : ";
				stream << fPacketsArrivedByPID[i] << " ";
			}//for
			stream << " failed waveform checks: " << fFailedWaveformChecks << " / "	<< fWaveformChecks << std::endl;
		}//void EventBuffer::Report(std::ostream& stream) const
	}  // namespace TargetDriver
}  // namespace CTA
