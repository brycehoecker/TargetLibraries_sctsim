// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#define BOOST_TEST_MODULE DATA_LISTENER
#include <boost/test/unit_test.hpp>

#include <thread>  // NOLINT(build/c++11), <thread> is supported by GCC 4.4.7

#include "TargetDriver/DataListener.h"
#include "TargetDriver/ModuleSimulator.h"

const uint8_t kNWavesPerPacket = 8;
const uint8_t kNSamplesPerWave = 128;

int SendDataPacket(CTA::TargetDriver::ModuleSimulator& simulator,  // NOLINT
                   CTA::TargetDriver::DataPacket& packet,          // NOLINT
                   uint32_t eventID, uint16_t packetID) {
  uint64_t tack = eventID*100; // event ID is set to TACK/100 in DataListner::Listen

  // These header items are not important for this unit test
  uint8_t slotID = 0;
  uint8_t eventSequenceNumber = 0;
  uint8_t quad = 0;
  uint8_t row = 0;
  uint8_t col = 0;

  // packetID = (detectorID[0-255]*64+asic[0-3]*16+ch[0-15])/kNWavesPerPacket

  uint32_t tmp = packetID * kNWavesPerPacket;
  uint8_t detectorID = uint8_t(tmp / 64);
  tmp %= 64;
  uint8_t asic = uint8_t(tmp / 16);
  tmp %= 16;
  uint8_t ch_offset = uint8_t((tmp / kNWavesPerPacket) * kNWavesPerPacket);

  packet.FillHeader(kNWavesPerPacket, kNSamplesPerWave, slotID, detectorID,
                    eventSequenceNumber, tack, quad, row, col);

  for (uint8_t i = 0; i < kNWavesPerPacket; ++i) {
    CTA::TargetDriver::Waveform* waveform = packet.GetWaveform(i);
    waveform->SetHeader(asic, static_cast<uint8_t>(ch_offset + i),
                        kNSamplesPerWave, false);
  }

  uint16_t pid;
  packet.GetPacketID(pid);
  BOOST_CHECK_EQUAL(pid, packetID);

  return simulator.SendDataPacket(packet.GetData(), packet.GetPacketSize());
}

BOOST_AUTO_TEST_CASE(TEST_DATA_LISTENER) {
  const uint16_t kNPacketsPerEvent = 256;  // = 2048/8
  const uint16_t kPacketSize = 2084;       // 8 waveforms with a 128-ns length
  const uint32_t kBufferDepth = 100;

  const double kTimeoutSec = 0.006;

  CTA::TargetDriver::DataPacket packet(kNWavesPerPacket, kNSamplesPerWave);

  std::string path = std::getenv("TARGET_DRIVER_CONFIG_DIR");
  if (path == "") {
    std::cerr << "TARGET_DRIVER_CONFIG_DIR is not set." << std::endl;
  }
  std::string defFPGA =
      path + "/older_firmware/TM5_FPGA_Firmware0xFEDA003C.def";
  std::string defASIC = path + "/T5_ASIC.def";

  CTA::TargetDriver::ModuleSimulator simulator("0.0.0.0", defFPGA, defASIC);
  simulator.Start();

  CTA::TargetDriver::TargetModule module(defFPGA, defASIC, 0);
  BOOST_CHECK_EQUAL(module.EstablishSlowControlLink("0.0.0.0", "0.0.0.0"),
                    TC_OK);

  CTA::TargetDriver::DataListener listener(kBufferDepth, kNPacketsPerEvent,
                                           kPacketSize, kTimeoutSec);
  BOOST_CHECK_EQUAL(listener.IsRunning(), false);
  BOOST_CHECK_EQUAL(listener.AddDAQListener("0.0.0.0"), TC_OK);
  listener.StartListening();
  BOOST_CHECK_EQUAL(listener.IsRunning(), true);

  auto buffer = listener.GetEventBuffer();

  // buffer is empty. should return zero.
  BOOST_CHECK_EQUAL(buffer->ReadEvent(), (CTA::TargetDriver::RawEvent*)NULL);

  uint32_t eventID = 0;

  // here we first check whether timed-out events are properly handled
  for (; eventID < kBufferDepth * 21 / 10; ++eventID) {
    // fill only partial packets
    for (uint16_t packetID = 0; packetID < kNPacketsPerEvent - 10; ++packetID) {
      BOOST_CHECK_EQUAL(SendDataPacket(simulator, packet, eventID, packetID),
                        TC_OK);
    }
    // Sleep a while to wait for the event buffer receive all the packets
    usleep(1000);
    // Write index should always point to the newest event
    BOOST_CHECK_EQUAL(buffer->GetWriteIndex(), eventID % kBufferDepth);
    // Read index should point to the same event, because we read an event every
    // time in this loop
    BOOST_CHECK_EQUAL(buffer->GetReadIndex(), eventID % kBufferDepth);
    // Finished index is always incremented in ReadEvent() when there are lost
    // packets
    BOOST_CHECK_EQUAL(
        buffer->GetFinishedIndex(),
        eventID == 0 ? kBufferDepth : (eventID - 1) % kBufferDepth);

    // intentionally make this event timed out
    usleep(static_cast<useconds_t>(kTimeoutSec * 1e6));

    auto event = buffer->ReadEvent();

    BOOST_CHECK_EQUAL(buffer->GetWriteIndex(), eventID % kBufferDepth);
    // Read index should be advanced by one after reading an event
    BOOST_CHECK_EQUAL(buffer->GetReadIndex(), (eventID + 1) % kBufferDepth);
    // Finished index is also advanced, because ReadEvent() checks if the next
    // event is timed out or not
    BOOST_CHECK_EQUAL(buffer->GetFinishedIndex(), eventID % kBufferDepth);

    BOOST_CHECK_EQUAL(event->GetEventHeader().GetEventID(), eventID);
    BOOST_CHECK_EQUAL(event->GetEventHeader().GetNPacketsFilled(),
                      kNPacketsPerEvent - 10);
    BOOST_CHECK_EQUAL(event->IsBeingBuilt(), true);
    BOOST_CHECK_EQUAL(event->IsTimedOut(), true);
    BOOST_CHECK_EQUAL(event->IsComplete(), false);
  }

  // Will try to send full packets
  for (; eventID < kBufferDepth * 52 / 10; ++eventID) {
    // fill all packets
    for (uint16_t packetID = 0; packetID < kNPacketsPerEvent; ++packetID) {
      BOOST_CHECK_EQUAL(SendDataPacket(simulator, packet, eventID, packetID),
                        TC_OK);
    }
    // Sleep a while to wait for the event buffer receive all the packets
    usleep(1000);
    BOOST_CHECK_EQUAL(buffer->GetWriteIndex(), eventID % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer->GetReadIndex(), eventID % kBufferDepth);
    // Finished index should point to last event. When an event is complete,
    // as finished index is incremented in AddNewPacket
    BOOST_CHECK_EQUAL(buffer->GetFinishedIndex(), eventID % kBufferDepth);

    // intentionally make this event timed out
    usleep(static_cast<useconds_t>(kTimeoutSec * 1e6));

    CTA::TargetDriver::RawEvent* event = buffer->ReadEvent();
    BOOST_CHECK(event != (CTA::TargetDriver::RawEvent*)NULL);

    BOOST_CHECK_EQUAL(buffer->GetWriteIndex(), eventID % kBufferDepth);
    // Only Read index is incremented in ReadEvent
    BOOST_CHECK_EQUAL(buffer->GetReadIndex(), (eventID + 1) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer->GetFinishedIndex(), eventID % kBufferDepth);

    BOOST_CHECK_EQUAL(event->GetEventHeader().GetEventID(), eventID);
    BOOST_CHECK_EQUAL(event->GetEventHeader().GetNPacketsFilled(),
                      kNPacketsPerEvent);
    BOOST_CHECK_EQUAL(event->IsBeingBuilt(), false);
    BOOST_CHECK_EQUAL(event->IsTimedOut(), true);
    BOOST_CHECK_EQUAL(event->IsComplete(), true);
  }

  // Will send full packets, and read events without time out
  for (; eventID < kBufferDepth * 81 / 10; ++eventID) {
    for (uint16_t packetID = 0; packetID < kNPacketsPerEvent; ++packetID) {
      BOOST_CHECK_EQUAL(SendDataPacket(simulator, packet, eventID, packetID),
                        TC_OK);
    }
    // Sleep a while to wait for the event buffer receive all the packets
    usleep(1000);
    BOOST_CHECK_EQUAL(buffer->GetWriteIndex(), eventID % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer->GetReadIndex(), eventID % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer->GetFinishedIndex(), eventID % kBufferDepth);

    CTA::TargetDriver::RawEvent* event = buffer->ReadEvent();
    BOOST_CHECK(event != (CTA::TargetDriver::RawEvent*)NULL);

    // Indices should behave the same as in the previous loop
    BOOST_CHECK_EQUAL(buffer->GetWriteIndex(), eventID % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer->GetReadIndex(), (eventID + 1) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer->GetFinishedIndex(), eventID % kBufferDepth);

    BOOST_CHECK_EQUAL(event->GetEventHeader().GetEventID(), eventID);
    BOOST_CHECK_EQUAL(event->GetEventHeader().GetNPacketsFilled(),
                      kNPacketsPerEvent);
    BOOST_CHECK_EQUAL(event->IsBeingBuilt(), false);
    BOOST_CHECK_EQUAL(event->IsTimedOut(), false);
    BOOST_CHECK_EQUAL(event->IsComplete(), true);
  }

  // Will send incomplete packets and remaining packets will be sent later
  for (; eventID < kBufferDepth * 82 / 10; ++eventID) {
    for (uint16_t packetID = 0; packetID < kNPacketsPerEvent - 10; ++packetID) {
      BOOST_CHECK_EQUAL(SendDataPacket(simulator, packet, eventID, packetID),
                        TC_OK);
    }
    // Sleep a while to wait for the event buffer receive all the packets
    usleep(1000);
    BOOST_CHECK_EQUAL(buffer->GetWriteIndex(), eventID % kBufferDepth);
    // Read and finished indices should not be incremented
    BOOST_CHECK_EQUAL(buffer->GetReadIndex(),
                      (kBufferDepth * 81 / 10) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer->GetFinishedIndex(),
                      (kBufferDepth * 81 / 10 - 1) % kBufferDepth);
  }

  for (uint16_t packetID = kNPacketsPerEvent - 10; packetID < kNPacketsPerEvent;
       ++packetID) {
    for (eventID = kBufferDepth * 81 / 10; eventID < kBufferDepth * 82 / 10;
         ++eventID) {
      BOOST_CHECK_EQUAL(SendDataPacket(simulator, packet, eventID, packetID),
                        TC_OK);
      // Sleep a while to wait for the event buffer receive all the packets
      usleep(1000);
      // Write index should keep pointing the newest event
      BOOST_CHECK_EQUAL(buffer->GetWriteIndex(),
                        (kBufferDepth * 82 / 10 - 1) % kBufferDepth);
      // Read and finished indices should not be incremented
      BOOST_CHECK_EQUAL(buffer->GetReadIndex(),
                        (kBufferDepth * 81 / 10) % kBufferDepth);
      if (packetID == kNPacketsPerEvent - 1) {
        // The last packets has arrived and this event is now complete
        BOOST_CHECK_EQUAL(buffer->GetFinishedIndex(), eventID % kBufferDepth);
      } else {
        BOOST_CHECK_EQUAL(buffer->GetFinishedIndex(),
                          (kBufferDepth * 81 / 10 - 1) % kBufferDepth);
      }
    }
  }

  for (eventID = kBufferDepth * 81 / 10; eventID < kBufferDepth * 82 / 10;
       ++eventID) {
    CTA::TargetDriver::RawEvent* event = buffer->ReadEvent();
    BOOST_CHECK(event != (CTA::TargetDriver::RawEvent*)NULL);
    BOOST_CHECK_EQUAL(event->GetEventHeader().GetEventID(), eventID);
    BOOST_CHECK_EQUAL(event->GetEventHeader().GetNPacketsFilled(),
                      kNPacketsPerEvent);
    // Write index should be remain at the same place
    BOOST_CHECK_EQUAL(buffer->GetWriteIndex(),
                      (kBufferDepth * 82 / 10 - 1) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer->GetReadIndex(), (eventID + 1) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer->GetFinishedIndex(),
                      (kBufferDepth * 82 / 10 - 1) % kBufferDepth);
  }

  // Will send incomplete packets without reading the event every time
  for (eventID = kBufferDepth * 82 / 10; eventID < kBufferDepth * 83 / 10;
       ++eventID) {
    for (uint16_t packetID = 0; packetID < kNPacketsPerEvent - 10; ++packetID) {
      BOOST_CHECK_EQUAL(SendDataPacket(simulator, packet, eventID, packetID),
                        TC_OK);
    }
    // Sleep a while to wait for the event buffer receive all the packets
    usleep(1000);
    BOOST_CHECK_EQUAL(buffer->GetWriteIndex(), eventID % kBufferDepth);
    // Read and finished indices should not be incremented
    BOOST_CHECK_EQUAL(buffer->GetReadIndex(),
                      (kBufferDepth * 82 / 10) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer->GetFinishedIndex(),
                      (kBufferDepth * 82 / 10 - 1) % kBufferDepth);
  }

  buffer->Flush();

  // Finished index should point last event because it was already flushed
  BOOST_CHECK_EQUAL(buffer->GetFinishedIndex(),
                    uint32_t(kBufferDepth * 83 / 10 - 1) % kBufferDepth);

  // Will send incomplete packets again without reading the event every time
  for (; eventID < kBufferDepth * 8.4; ++eventID) {
    for (uint16_t packetID = 0; packetID < kNPacketsPerEvent - 10; ++packetID) {
      // Cannot add this packet any more after flushing
      BOOST_CHECK_EQUAL(SendDataPacket(simulator, packet, eventID, packetID),
                        TC_OK);
    }
    // Sleep a while to wait for the event buffer receive all the packets
    usleep(1000);
    BOOST_CHECK_EQUAL(buffer->GetWriteIndex(),
                      (kBufferDepth * 83 / 10 - 1) % kBufferDepth);
    // Read and finished indices should not be incremented
    BOOST_CHECK_EQUAL(buffer->GetReadIndex(),
                      (kBufferDepth * 82 / 10) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer->GetFinishedIndex(),
                      (kBufferDepth * 83 / 10 - 1) % kBufferDepth);
  }

  // Wait for std::cerr to be flushed. Otherwise two cerr messages made by two
  // threads will mix up.
  usleep(20000);

  // Read events waiting to be read
  for (eventID = kBufferDepth * 82 / 10; eventID < kBufferDepth * 83 / 10;
       ++eventID) {
    CTA::TargetDriver::RawEvent* event = NULL;
    while (event == NULL) {
      event = buffer->ReadEvent();
    }

    BOOST_CHECK_EQUAL(event->GetEventHeader().GetEventID(), eventID);
    BOOST_CHECK_EQUAL(event->GetEventHeader().GetNPacketsFilled(),
                      kNPacketsPerEvent - 10);
    BOOST_CHECK_EQUAL(event->WasFlushed(), true);
    // Write index should be remain at the same place
    BOOST_CHECK_EQUAL(buffer->GetWriteIndex(),
                      (kBufferDepth * 83 / 10 - 1) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer->GetReadIndex(), (eventID + 1) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer->GetFinishedIndex(),
                      (kBufferDepth * 83 / 10 - 1) % kBufferDepth);
  }

  // Try to read events that were added after flushing the buffer-> It should
  // be empty.
  for (; eventID < kBufferDepth * 84 / 10; ++eventID) {
    auto event = buffer->ReadEvent();
    BOOST_CHECK_EQUAL(event, (CTA::TargetDriver::RawEvent*)NULL);
    BOOST_CHECK_EQUAL(buffer->GetWriteIndex(),
                      (kBufferDepth * 83 / 10 - 1) % kBufferDepth);
    // Read and finished indices should not be incremented
    BOOST_CHECK_EQUAL(buffer->GetReadIndex(),
                      (kBufferDepth * 83 / 10) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer->GetFinishedIndex(),
                      (kBufferDepth * 83 / 10 - 1) % kBufferDepth);
  }
}
