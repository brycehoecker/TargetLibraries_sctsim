// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include <fstream>
#include "TargetDriver/DataListener_v2.h"

namespace CTA {
namespace TargetDriver {

DataListener_v2::DataListener_v2(uint32_t pBufferDepth, uint16_t pNPacketsPerEvent,
				 uint16_t pPacketSize, float pBuildTimeout,
				 uint32_t pCheckFreq)
    : UDPClient(),
      fNPacketsReceived(0),
      fNPacketProblems(0),
      fEventBuffer(std::make_shared<EventBuffer_v2>(pBufferDepth,pNPacketsPerEvent, pPacketSize,pBuildTimeout, pCheckFreq)),
      fRunning(false),
      fDropPackets(false) {}

DataListener_v2::~DataListener_v2() { StopListening(); }

/// Continuously receive data packets from the server and add them to the event
/// buffer
void DataListener_v2::Listen() {
  //  uint32_t eventID;
  uint16_t packetID;

  DataPacket_v2* dataPacket;

  bool print_errors = true;

  std::ofstream tack_file;
  tack_file.open("/home/cta/TACK_times.dat", std::ofstream::app);

  while (fRunning) {
    if (fNPacketProblems > 100 && print_errors) {
      std::cerr << "GetDataPacket: over 100 packet problems - suppressing further print statements"  << std::endl;
      print_errors = false;
    }
    
    dataPacket=fEventBuffer->GetAvailableDataPacket(); //Provides next data packet available to write
    if (NULL==dataPacket) {
      usleep(100);
      continue;
    }

    uint32_t bytes = 0;
    uint8_t* data = dataPacket->GetData();
    int ret = GetDataPacket(reinterpret_cast<void*>(data), bytes, dataPacket->GetPacketSize());
    switch (ret) {
      case TC_OK:                        // do nothing
        break;
      case TC_TIME_OUT:                  // It's OK. Let's wait for a packet.
        continue;
      case TC_ERR_COMM_FAILURE:          // TODO(Akira): Error handling
        std::cerr << "GetDataPacket Problem: TC_ERR_COMM_FAILURE" << std::endl;
        continue;
      default:                           // Something wrong
        std::cerr << "GetDataPacket Problem: Unknown - SHOULD NEVER HAPPEN" << std::endl;
        continue;
    }

    if (bytes != dataPacket->GetPacketSize()) {
      // TODO(Akira): Error handling. I think this packet should be saved in a
      // file as well, because we must investigate the reason of malformation.
      if (print_errors)
        std::cout << "DataListener::Listen() - Data packet is not the expected size - was " \
		  << bytes << " - expected " << dataPacket->GetPacketSize()  << " - " \
		  << dataPacket->GetStatusString() << std::endl;
      ++fNPacketProblems;
      continue;
    }

    if (!dataPacket->GetPacketID(packetID)) {
      // Packet ID was not calculated - packet is invalid or there are no
      // waveforms
      // TODO(Akira): Error handling
      if (print_errors)
        std::cout << "DataListener::Listen() Could not calculate the packet ID - status code: " \
                  << dataPacket->GetStatus() << " - " << dataPacket->GetStatusString() << std::endl;
      ++fNPacketProblems;
      continue;
    }

    // Use TACK stamp as event ID. This should be OK as long as TACK is always
    // properly set and unique.
    // TODO(Jim): Casting uint64_t to uint32_t is not safe here. Event ID was
    // first introduced to hold sequential integers. If we really want to use
    // uint64_t for event IDs, event header format and the corresponding FITS
    // header must be updated.
    //eventID = (uint32_t)(dataPacket->GetTACKTime() / 100);
    // Jim - 100 ns precision is sufficient - work around...
    
    ++fNPacketsReceived;
    // TODO(Akira): Change the packet ID type from uint32_t to uint16_t once
    // it is changed in TargetDriver::DataPacket

    /////////////////////////////////////
    if (!fDropPackets){
      //Add Packet to the DataPacket buffer;
      fEventBuffer->PushAvailableDataPacket(dataPacket);
      //Try assign the packet to an event: NOTE: This could be done in a separate thread!!!!!
      fEventBuffer->BuildSingleDataPacket();
    } else if (packetID == 0) {
      tack_file << static_cast<int>(dataPacket->GetStaleBit()) << '\t' << dataPacket->GetTACKTime() << std::endl;
    }
  }
}

/*!
@brief Starts the Listen method
*/
void DataListener_v2::StartListening() {
  if (IsRunning()) {
    return;
  }

  fRunning = true;
  std::cout << "DataListener::StartListening() - reseting counters - previous "
               "good packets received = "
            << fNPacketsReceived << " and rejected: " << fNPacketProblems
            << std::endl;
  fNPacketProblems = 0;
  fThread = std::thread(&DataListener_v2::Listen, this);
}

/*!
@brief Stops the Listen method
*/
void DataListener_v2::StopListening() {
  if (!IsRunning()) {
    return;
  }

  fRunning = false;
  if (fThread.joinable()) {
    std::cout << "StopListening - wait for thread to join" << std::endl;
    fThread.join();
    //usleep(1000);
    // fThread.stop_thread();
    std::cout << " - joined" << std::endl;
  }
  //  delete &fThread;
}

}  // namespace TargetDriver
}  // namespace CTA
