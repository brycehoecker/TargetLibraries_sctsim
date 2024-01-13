#include <ostream>
#include <iomanip>
#include "TargetDriver/EventBuffer_v2.h"

namespace CTA {
namespace TargetDriver {
  //----------------------------------------------------------------------
  EventBuffer_v2::EventBuffer_v2(uint32_t pBufferDepth, uint16_t pNPacketsPerEvent, uint16_t pPacketSize,
				 float pBuildTimeout, uint32_t pCheckFreq)
    : fEventBuffer(pBufferDepth), fDataPacketBuffer(pBufferDepth*pNPacketsPerEvent) {
    float bufferGbs = 1e-9f * pBufferDepth * pNPacketsPerEvent * pPacketSize;

    // NOTE(MBG): Could make the DataPacket vector a bigger size than the event vector.
    std::cout << "Allocating " << bufferGbs << " GB for EventBuffer" << std::endl;

    fDataPacketVector.resize(fDataPacketBuffer.GetCapacity());
    for (auto it = fDataPacketVector.begin(); it != fDataPacketVector.end(); ++it) {
      (*it) = new DataPacket_v2(pPacketSize);
    }

    fEventVector.resize(fEventBuffer.GetCapacity());
    for (auto it = fEventVector.begin(); it != fEventVector.end(); ++it) {
      (*it) = new RawEvent_v2(pNPacketsPerEvent, pPacketSize,false);
      (*it)->SetTimeoutSec(pBuildTimeout);
    }

    fCheckFreq = pCheckFreq;
    fPacketsArrivedByPID.resize(pNPacketsPerEvent, 0);
    Clear();
  }

  EventBuffer_v2::~EventBuffer_v2() {
    ClearEvents();
    for (auto it = fEventVector.begin(); it != fEventVector.end(); ++it) {
      delete (*it);
    }
    for (auto it = fDataPacketVector.begin(); it != fDataPacketVector.end(); ++it) {
      delete (*it);
    }
  }

  //----------------------------------------------------------------------
  void EventBuffer_v2::Clear() {
    ClearEvents();
    InitializeMembers();
  }

  //----------------------------------------------------------------------
  void EventBuffer_v2::ClearEvents() {
    for (auto it = fEventVector.begin(); it != fEventVector.end(); ++it) {
      (*it)->Clear();
      for (uint cnt = 0 ; cnt < (*it)->GetNPacketsPerEvent(); ++cnt) { (*it)->DissociatePacket(cnt); }
    }
  }

  //----------------------------------------------------------------------
  void EventBuffer_v2::InitializeMembers() {
    fEventBuffer.Clear();
    fDataPacketBuffer.Clear();
    fFlushed = false;
    fPacketsArrived = fPacketsDropped = 0;
    fEventsBuilt = fEventsRead = fEventsTimedOut = fEventsForcedOut = fEventsOverwritten = 0;
    fWaveformChecks = fFailedWaveformChecks = 0;
    for (uint32_t i = 0; i < fPacketsArrivedByPID.size(); ++i) { fPacketsArrivedByPID[i] = 0; }
  }

  //----------------------------------------------------------------------
  DataPacket_v2* EventBuffer_v2::GetAvailableDataPacket (){
    if (fDataPacketBuffer.IsFull()) { return NULL; }
    else return fDataPacketVector[fDataPacketBuffer.GetWriteIndex()];
  }

  //----------------------------------------------------------------------
  bool EventBuffer_v2::PushAvailableDataPacket(DataPacket_v2 *pDataPacket) {
    if (pDataPacket!=fDataPacketVector[fDataPacketBuffer.GetWriteIndex()]) { return false; }
    pDataPacket->SetFilled(true);
    return fDataPacketBuffer.IncWriteIndex();
  }

  //----------------------------------------------------------------------
  //Checks if there is an incoming (not built) DataPacket in the PacketBuffer and tries to match it to an Event
  bool EventBuffer_v2::BuildSingleDataPacket() {
    static RawEvent_v2 *iLastEventMatch=NULL;
    static bool flushErrorMessageWasPrinted = false;
    RawEvent_v2 *iEventToAssociate=NULL;

    // check if there are incoming data packets not being built
    if (fDataPacketBuffer.GetBuildIndex()==fDataPacketBuffer.GetWriteIndex()) { return false; }
    auto iDataPacket=GetDataPacketAtIndex(fDataPacketBuffer.GetBuildIndex());
    uint16_t iPacketID;
    if (!iDataPacket->GetPacketID(iPacketID)) { std::cerr << "Cannot Calculate PacketID\n"; }
    else {
      // MBG: HACK!!!! use the TACK to generate an EventID
      uint32_t iEventID = (uint32_t)(iDataPacket->GetTACKTime() / 100);
      //      std::cout << "EvID:" << iEventID << " PID:" << iPacketID << " ";
      if ( fFlushed ) {
	if (!flushErrorMessageWasPrinted) {
	  std::cerr << "Packet arrived after Flush() - ignoring packet "  << iPacketID
		    << " of event " << iEventID << " and all packets later\n";
	}
	flushErrorMessageWasPrinted = true;
      } else {
	++fPacketsArrived;
	if ( iPacketID >= fPacketsArrivedByPID.size() ) {
	  std::cerr << "Unexpected packet ID arrived at buffer" << std::endl;
	} else {
	  ++fPacketsArrivedByPID[iPacketID];
	  // Let's try to see if the last event match had the same eventID. Should check wasRead and IsBeingBuilt?
	  if ( iLastEventMatch != NULL ) {
	    if ( iLastEventMatch->GetEventHeader().GetEventID() == iEventID ) {
	      //	      std::cout << "Match LastEvent ";
	      iEventToAssociate=iLastEventMatch;
	    }
	  }
	  // If we didn't find a match, let's try to find it in the whole Event Buffer.
	  // Should check wasRead and IsBeingBuilt?
	  if ( !iEventToAssociate ) {
	    for (auto it=fEventBuffer.GetReadIndex();it!=fEventBuffer.GetWriteIndex();it=fEventBuffer.NextIndex(it) ) {
	      if (GetEventAtIndex(it)->GetEventHeader().GetEventID() == iEventID) {
		//		std::cout << "Match Buffer:" << it << " ";
		iEventToAssociate=GetEventAtIndex(it);
	      }
	    }
	  }
	  //If we didnt't find a match still, let's try to get an unused free event
	  if ( !iEventToAssociate ) {
	    if ( !fEventBuffer.IsFull() ) {
	      //	      std::cout << "No Match, create Event ";
	      auto event = GetEventAtIndex(fEventBuffer.GetWriteIndex());
	      if ( !event->IsEmpty() && !event->WasRead() ) { fEventsOverwritten++; }
	      iEventToAssociate=event;
	      event->Clear();
	      event->GetEventHeader().SetEventID(iEventID);
	      if ( !fEventBuffer.IncWriteIndex() ) {
		std::cerr << "Failure when writting to Event Buffer" << std::endl;
	      }
	    }
	  }
	  // We ran all checks and looked for a match, now is time to do the actual association
	  if ( iEventToAssociate ) {
	    iEventToAssociate->AssociatePacket(iDataPacket,iPacketID, false);
	    iLastEventMatch=iEventToAssociate;
	  }
	}
      }
    }
    // Drop packets if they failed to associate to any event
    if ( !iEventToAssociate ) {
      ++fPacketsDropped;
      iDataPacket->SetProcessed(true);
    }
    fDataPacketBuffer.IncBuildIndex();
    //    std::cout << std::endl;
    return true;
  }

  //----------------------------------------------------------------------
  RawEvent_v2* EventBuffer_v2::ReadEvent () {
    RawEvent_v2* iEventToReturn=NULL;
    if ( !fEventBuffer.IsEmpty() ) {
      auto iEvent=GetEventAtIndex(fEventBuffer.GetReadIndex());
      if ( !iEvent->WasRead() ) {
	// If the event is complete and not read yet, then is the one to be read now
	if ( iEvent->IsComplete() ) {
	  ++fEventsBuilt;
	  iEventToReturn = iEvent;
	  // An incomplete event will be read if it timed-out, it was flushed or the buffer is too full.
	} else if ( iEvent->IsBeingBuilt() ) {
	  if ( iEvent -> WasFlushed() ) {	   //Is the event flushed?
	    iEventToReturn = iEvent;
	    std::cerr << "Event " << iEvent->GetEventHeader().GetEventID() << " was flushed - had filled "
		      << iEvent->GetEventHeader().GetNPacketsFilled() << " packets.\n";
	  }	else if ( iEvent->IsTimedOut() ) { //Did the event timeout?
	    ++fEventsTimedOut;
	    iEventToReturn = iEvent;
	    if ( (fEventsTimedOut & 0x3FF) == 0) {
	      std::cerr << "Event " << iEvent->GetEventHeader().GetEventID() << " timed out - had filled "
			<< iEvent->GetEventHeader().GetNPacketsFilled() << " packets - have now timed out on "
			<< fEventsTimedOut << " events \n";
	    }
	  } else if ( (1.1*fEventBuffer.GetCount()) > fEventBuffer.GetCapacity() ){ // is the buffer too full?
	    ++fEventsForcedOut;
	    iEventToReturn = iEvent;
	    if ((fEventsForcedOut & 0x3FF) == 0) {
	      std::cerr << "Event " << iEvent->GetEventHeader().GetEventID()
			<< " was removed because Event Buffer was almost full (" << fEventBuffer.GetCount()
			<< "/" << fEventBuffer.GetCapacity() << ") - had filled "
			<< iEvent->GetEventHeader().GetNPacketsFilled() << " packets - have now forced out on "
			<< fEventsForcedOut << " events \n";
	    }
	  }
	}
      }
    }
    return iEventToReturn;
  }

  //----------------------------------------------------------------------
  bool EventBuffer_v2::ClearProcessedDataPackets() {
    while (!fDataPacketBuffer.IsEmpty() && GetDataPacketAtIndex(fDataPacketBuffer.GetReadIndex())->IsProcessed()) {
      GetDataPacketAtIndex(fDataPacketBuffer.GetReadIndex())->Clear();
      fDataPacketBuffer.IncReadIndex();
    }
    return true;
  }

  //----------------------------------------------------------------------
  bool EventBuffer_v2::ClearProcessedEvents() {
    while (!fEventBuffer.IsEmpty() && GetEventAtIndex(fEventBuffer.GetReadIndex())->WasRead()) {
      ++fEventsRead;
      GetEventAtIndex(fEventBuffer.GetReadIndex())->Clear();
      GetEventAtIndex(fEventBuffer.GetReadIndex())->DissociateAllPackets();
      fEventBuffer.IncReadIndex();
    }
    return true;
  }

  //----------------------------------------------------------------------
  void EventBuffer_v2::Flush() {
    if (fEventBuffer.IsEmpty()) return;
    fFlushed=true;
    for (auto it=fEventBuffer.GetReadIndex(); it!=fEventBuffer.GetWriteIndex(); it=fEventBuffer.NextIndex(it)) {
      if ( GetEventAtIndex(it)->IsBeingBuilt() ) { GetEventAtIndex(it)->SetToFlushed(); }
    }
  }

  //----------------------------------------------------------------------
  bool EventBuffer_v2::StatusOK() const {
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
    return true;
  }

  //----------------------------------------------------------------------
  float EventBuffer_v2::GetEventRate() {
    static uint64_t oldtime=getTimeStamp();
    static uint64_t oldnpin=0;
    //	static uint64_t oldnein=0;
    static uint64_t oldneout=0;

    //    std::cout << "GetEventRate()" << std::endl;
    uint64_t ntot = fPacketsArrived;
    uint64_t nbad = fPacketsDropped;
    //  uint64_t netot = ntot/fPacketsArrivedByPID.size();
    uint64_t curtime=getTimeStamp();
    double   dtime=(static_cast<double>(curtime-oldtime))/1e9;
    double   ratepin = (static_cast<double>(ntot-oldnpin))/dtime;
    //  double   ratein = (static_cast<double>(netot-oldnein))/dtime;
    double   rateout = (static_cast<double>(fEventsRead-oldneout))/dtime;
    oldtime=curtime;
    oldnpin=ntot;
    //	oldnein=netot;
    oldneout=fEventsRead;
    double   occpack = 100.0*(static_cast<double>(fDataPacketBuffer.GetCount()))/
      static_cast<double>(fDataPacketBuffer.GetCapacity());
    double   occevnt = 100.0*(static_cast<double>(fEventBuffer.GetCount()))/
      static_cast<double>(fEventBuffer.GetCapacity());
    std::cout << "LoopT: " << std::setprecision(2) << dtime << "s "
	      << "PacketIn: " << ntot << " (" << std::setprecision(6) << ratepin << "/s) "
	      << "EventOut: "<< fEventsRead <<  " (" << std::setprecision(5) << rateout << "/s) "
	      << "P.Buff: " << fDataPacketBuffer.GetCapacity() << " (" << std::setprecision(3) << occpack << "% used) "
	      << "E.Buff: " << fEventBuffer.GetCapacity() << " (" << std::setprecision(3) << occevnt << "% used) "
	      << "P.Bad: " << nbad << std::endl;
    //    std::cout << "GetEventRate() done" << std::endl;
    return rateout;
  }

  //----------------------------------------------------------------------
  void EventBuffer_v2::Report(std::ostream& stream) const {
    stream  << "EventBuffer::Report | Packets received: " << fPacketsArrived << " and dropped: " << fPacketsDropped
	    << " - Events built " << fEventsBuilt << " timed out " << fEventsTimedOut
	    << " forced out " << fEventsForcedOut  << " read " << fEventsRead
	    << " overwritten " << fEventsOverwritten << std::endl;
    stream  << "Number of packets that have arrived - by packet ID: ";
    for (unsigned int i = 0; i < fPacketsArrivedByPID.size(); ++i) {
      if ((i % 16) == 0) stream << std::endl;
      if ((i % 8) == 0) stream << "\t" << std::setw(3) << i << " to " << std::setw(3) << i + 7 << " : ";
      stream << std::setw(5) << fPacketsArrivedByPID[i] << " ";
    }
    stream << std::endl << " failed waveform checks: " << fFailedWaveformChecks << " / "
	   << fWaveformChecks << std::endl;
  }

  //----------------------------------------------------------------------
  void EventBuffer_v2::DiagnosticReport(std::ostream& stream) const {
    stream << "index \t evid \t is_being_built \t complete \t was_read \t is_empty" << std::endl;
    for (int64_t it=0; it < fEventBuffer.GetCapacity(); it++) {
      auto ev=GetEventAtIndex(it);
      stream << it << "\t" << ev->GetEventHeader().GetEventID() << "\t" << ev->IsBeingBuilt() << "\t"
	     << ev->IsComplete() << "\t" << ev->WasRead() << "\t" << ev->IsEmpty() << std::endl;
    }
  }

}  // namespace TargetDriver
}  // namespace CTA
