// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include "TargetDriver/RawEvent_v2.h"

namespace CTA {
namespace TargetDriver {
  //----------------------------------------------------------------------
  RawEvent_v2::RawEvent_v2(uint16_t pNPacketsPerEvent, uint16_t pPacketSize,bool pCreatePackets)
    : fTimeoutSec(0.3),fTimedOut(false) {
    fDataPackets.resize(pNPacketsPerEvent);
    for (auto it = fDataPackets.begin(); it != fDataPackets.end(); ++it) {
      if (pCreatePackets) { (*it)= new DataPacket_v2(pPacketSize); }
      else { (*it)=NULL; }
    }
    Clear();
  }

  //----------------------------------------------------------------------
  /// Initialize the internal states and clear data packets' flag.
  void RawEvent_v2::Clear() {
    fTimedOut = false;
    fFlushed = false;
    fRead = false;
    fWaveformCheckStatus = true;
    fEventHeader.Init();  //Why not Clear?
    for (auto it = fDataPackets.begin(); it != fDataPackets.end(); ++it) {
      if ((*it)!=NULL) { (*it)->Clear(); }
    }
  }

  //----------------------------------------------------------------------
  // Associate an already existing packet to this RawEvent
  bool RawEvent_v2::AssociatePacket (DataPacket_v2* pDataPacket, uint16_t pPacketID, bool pCheckFlag) {
    if (pPacketID >= fDataPackets.size()) {
      std::cerr << "RawEvent::AssociatePacket - Bad Packet ID: " << pPacketID;
      return false;
    }
    if (fDataPackets[pPacketID]!=NULL) {
      //Oooops, there is already a packet assigned there... Bad things could happen! Should drop it...
      std::cerr << "RawEvent::AssociatePacket - Packet ID already associated: " << pPacketID;
      return false;
    }
    fDataPackets[pPacketID]=pDataPacket;
    fDataPackets[pPacketID]->SetBuilt(true);
    if (fEventHeader.GetNPacketsFilled() == 0) {
      fEventHeader.SetTimeStampNow();
      fEventHeader.SetTACK(pDataPacket->GetTACKTime());
    }
    fEventHeader.IncrementNPacketsFilled();
    if (pCheckFlag) {
      Waveform* w = pDataPacket->GetWaveform(0);
      float rms, mean;
      w->GetMeanAndRMS(mean, rms, 10);
      ///      std::cout << "Check: " << mean << " " << rms << std::endl;
      fWaveformCheckStatus = ((mean < 900.0) && (rms < 100.0));
      if (!fWaveformCheckStatus) {
        std::cerr << "RawEvent::AssignPacket - Suspicious waveform - mean "  << mean << " rms " << rms << std::endl;
      }
    }
    return true;
  }

  //----------------------------------------------------------------------
  // Dissociate one of the dataPackets from this RawEvent
  bool RawEvent_v2::DissociatePacket (uint16_t pPacketID) {
    if (pPacketID >= fDataPackets.size()) {
      std::cerr << "RawEvent::DissociatePacket - Bad Packet ID: " << pPacketID;
      return false;
    }
    if (fDataPackets[pPacketID]!=NULL) { fDataPackets[pPacketID]->SetProcessed(true); }
    fDataPackets[pPacketID]=NULL;
    return true;
  }

  //----------------------------------------------------------------------
  bool RawEvent_v2::DissociateAllPackets (){
    for (uint i=0;i<fDataPackets.size();++i) {
      if (fDataPackets[i]!=NULL) { fDataPackets[i]->SetProcessed(true); }
      fDataPackets[i]=NULL;
    }
    return true;
  }
}  // namespace TargetDriver
}  // namespace CTA
