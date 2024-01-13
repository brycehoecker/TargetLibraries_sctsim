// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#define BOOST_TEST_MODULE EVENT_BUFFER
#include <boost/test/unit_test.hpp>

#include "TargetDriver/EventBuffer.h"

BOOST_AUTO_TEST_CASE(TEST_EVENT_BUFFER) {
  const uint16_t kNPacketsPerEvent = 256;  // = 2048/8
  const uint16_t kPacketSize = 2084;       // 8 waveforms with a 128-ns length
  const uint32_t kBufferDepth = 100;

  // this is the minimum value that does not make any errors on Akira's Mac
  // (Core i7 2.8 GHz + 16 GB 1600 MHz DDR3 memory) when kBufferDepth is 100
  // So EventBuffer::AddNewPacket can run at a trigger rate of up to ~2.5 kHz
  const double kTimeoutSec = 0.004;

  uint8_t* data = new uint8_t[kPacketSize];

  CTA::TargetDriver::EventBuffer buffer(kBufferDepth, kNPacketsPerEvent,
                                        kPacketSize, kTimeoutSec);

  // buffer is empty. should return zero.
  BOOST_CHECK_EQUAL(buffer.ReadEvent(), (CTA::TargetDriver::RawEvent*)NULL);

  uint32_t eventID = 0;

  // here we first check whether timed-out events are properly handled
  for (; eventID < kBufferDepth * 21 / 10; ++eventID) {
    // fill only partial packets
    for (uint16_t packetID = 0; packetID < kNPacketsPerEvent - 10; ++packetID) {
      BOOST_CHECK_EQUAL(
          buffer.AddNewPacket(data, eventID, packetID, kPacketSize), true);
    }
    // Write index should always point to the newest event
    BOOST_CHECK_EQUAL(buffer.GetWriteIndex(), eventID % kBufferDepth);
    // Read index should point to the same event, because we read an event every
    // time in this loop
    BOOST_CHECK_EQUAL(buffer.GetReadIndex(), eventID % kBufferDepth);
    // Finished index is always incremented in ReadEvent() when there are lost
    // packets
    BOOST_CHECK_EQUAL(
        buffer.GetFinishedIndex(),
        eventID == 0 ? kBufferDepth : (eventID - 1) % kBufferDepth);

    // intentionally make this event timed out
    usleep(static_cast<useconds_t>(kTimeoutSec * 1e6));

    auto event = buffer.ReadEvent();

    BOOST_CHECK_EQUAL(buffer.GetWriteIndex(), eventID % kBufferDepth);
    // Read index should be advanced by one after reading an event
    BOOST_CHECK_EQUAL(buffer.GetReadIndex(), (eventID + 1) % kBufferDepth);
    // Finished index is also advanced, because ReadEvent() checks if the next
    // event is timed out or not
    BOOST_CHECK_EQUAL(buffer.GetFinishedIndex(), eventID % kBufferDepth);

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
      BOOST_CHECK_EQUAL(
          buffer.AddNewPacket(data, eventID, packetID, kPacketSize), true);
    }
    BOOST_CHECK_EQUAL(buffer.GetWriteIndex(), eventID % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer.GetReadIndex(), eventID % kBufferDepth);
    // Finished index should point to last event. When an event is complete,
    // as finished index is incremented in AddNewPacket
    BOOST_CHECK_EQUAL(buffer.GetFinishedIndex(), eventID % kBufferDepth);

    // intentionally make this event timed out
    usleep(static_cast<useconds_t>(kTimeoutSec * 1e6));

    CTA::TargetDriver::RawEvent* event = buffer.ReadEvent();
    BOOST_CHECK(event != (CTA::TargetDriver::RawEvent*)NULL);

    BOOST_CHECK_EQUAL(buffer.GetWriteIndex(), eventID % kBufferDepth);
    // Only Read index is incremented in ReadEvent
    BOOST_CHECK_EQUAL(buffer.GetReadIndex(), (eventID + 1) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer.GetFinishedIndex(), eventID % kBufferDepth);

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
      BOOST_CHECK_EQUAL(
          buffer.AddNewPacket(data, eventID, packetID, kPacketSize), true);
    }
    BOOST_CHECK_EQUAL(buffer.GetWriteIndex(), eventID % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer.GetReadIndex(), eventID % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer.GetFinishedIndex(), eventID % kBufferDepth);

    CTA::TargetDriver::RawEvent* event = buffer.ReadEvent();
    BOOST_CHECK(event != (CTA::TargetDriver::RawEvent*)NULL);

    // Indices should behave the same as in the previous loop
    BOOST_CHECK_EQUAL(buffer.GetWriteIndex(), eventID % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer.GetReadIndex(), (eventID + 1) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer.GetFinishedIndex(), eventID % kBufferDepth);

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
      BOOST_CHECK_EQUAL(
          buffer.AddNewPacket(data, eventID, packetID, kPacketSize), true);
    }
    BOOST_CHECK_EQUAL(buffer.GetWriteIndex(), eventID % kBufferDepth);
    // Read and finished indices should not be incremented
    BOOST_CHECK_EQUAL(buffer.GetReadIndex(),
                      (kBufferDepth * 81 / 10) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer.GetFinishedIndex(),
                      (kBufferDepth * 81 / 10 - 1) % kBufferDepth);
  }

  for (uint16_t packetID = kNPacketsPerEvent - 10; packetID < kNPacketsPerEvent;
       ++packetID) {
    for (eventID = kBufferDepth * 81 / 10; eventID < kBufferDepth * 82 / 10;
         ++eventID) {
      BOOST_CHECK_EQUAL(
          buffer.AddNewPacket(data, eventID, packetID, kPacketSize), true);
      // Write index should keep pointing the newest event
      BOOST_CHECK_EQUAL(buffer.GetWriteIndex(),
                        (kBufferDepth * 82 / 10 - 1) % kBufferDepth);
      // Read and finished indices should not be incremented
      BOOST_CHECK_EQUAL(buffer.GetReadIndex(),
                        (kBufferDepth * 81 / 10) % kBufferDepth);
      if (packetID == kNPacketsPerEvent - 1) {
        // The last packets has arrived and this event is now complete
        BOOST_CHECK_EQUAL(buffer.GetFinishedIndex(), eventID % kBufferDepth);
      } else {
        BOOST_CHECK_EQUAL(buffer.GetFinishedIndex(),
                          (kBufferDepth * 81 / 10 - 1) % kBufferDepth);
      }
    }
  }

  for (eventID = kBufferDepth * 81 / 10; eventID < kBufferDepth * 82 / 10;
       ++eventID) {
    CTA::TargetDriver::RawEvent* event = buffer.ReadEvent();
    BOOST_CHECK(event != (CTA::TargetDriver::RawEvent*)NULL);
    BOOST_CHECK_EQUAL(event->GetEventHeader().GetEventID(), eventID);
    BOOST_CHECK_EQUAL(event->GetEventHeader().GetNPacketsFilled(),
                      kNPacketsPerEvent);
    // Write index should be remain at the same place
    BOOST_CHECK_EQUAL(buffer.GetWriteIndex(),
                      (kBufferDepth * 82 / 10 - 1) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer.GetReadIndex(), (eventID + 1) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer.GetFinishedIndex(),
                      (kBufferDepth * 82 / 10 - 1) % kBufferDepth);
  }

  // Will send incomplete packets without reading the event every time
  for (eventID = kBufferDepth * 82 / 10; eventID < kBufferDepth * 83 / 10;
       ++eventID) {
    for (uint16_t packetID = 0; packetID < kNPacketsPerEvent - 10; ++packetID) {
      BOOST_CHECK_EQUAL(
          buffer.AddNewPacket(data, eventID, packetID, kPacketSize), true);
    }
    BOOST_CHECK_EQUAL(buffer.GetWriteIndex(), eventID % kBufferDepth);
    // Read and finished indices should not be incremented
    BOOST_CHECK_EQUAL(buffer.GetReadIndex(),
                      (kBufferDepth * 82 / 10) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer.GetFinishedIndex(),
                      (kBufferDepth * 82 / 10 - 1) % kBufferDepth);
  }

  buffer.Flush();

  // Finished index should point last event because it was already flushed
  BOOST_CHECK_EQUAL(buffer.GetFinishedIndex(),
                    uint32_t(kBufferDepth * 83 / 10 - 1) % kBufferDepth);

  // Will send incomplete packets again without reading the event every time
  for (; eventID < kBufferDepth * 8.4; ++eventID) {
    for (uint16_t packetID = 0; packetID < kNPacketsPerEvent - 10; ++packetID) {
      // Cannot add this packet any more after flushing
      BOOST_CHECK_EQUAL(
          buffer.AddNewPacket(data, eventID, packetID, kPacketSize), false);
    }
    BOOST_CHECK_EQUAL(buffer.GetWriteIndex(),
                      (kBufferDepth * 83 / 10 - 1) % kBufferDepth);
    // Read and finished indices should not be incremented
    BOOST_CHECK_EQUAL(buffer.GetReadIndex(),
                      (kBufferDepth * 82 / 10) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer.GetFinishedIndex(),
                      (kBufferDepth * 83 / 10 - 1) % kBufferDepth);
  }

  // Read events waiting to be read
  for (eventID = kBufferDepth * 82 / 10; eventID < kBufferDepth * 83 / 10;
       ++eventID) {
    CTA::TargetDriver::RawEvent* event = NULL;
    while (event == NULL) {
      event = buffer.ReadEvent();
    }

    BOOST_CHECK_EQUAL(event->GetEventHeader().GetEventID(), eventID);
    BOOST_CHECK_EQUAL(event->GetEventHeader().GetNPacketsFilled(),
                      kNPacketsPerEvent - 10);
    BOOST_CHECK_EQUAL(event->WasFlushed(), true);
    // Write index should be remain at the same place
    BOOST_CHECK_EQUAL(buffer.GetWriteIndex(),
                      (kBufferDepth * 83 / 10 - 1) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer.GetReadIndex(), (eventID + 1) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer.GetFinishedIndex(),
                      (kBufferDepth * 83 / 10 - 1) % kBufferDepth);
  }

  // Try to read events that were added after flushing the buffer. It should
  // be empty.
  for (; eventID < kBufferDepth * 84 / 10; ++eventID) {
    CTA::TargetDriver::RawEvent* event = buffer.ReadEvent();
    BOOST_CHECK_EQUAL(event, (CTA::TargetDriver::RawEvent*)NULL);
    BOOST_CHECK_EQUAL(buffer.GetWriteIndex(),
                      (kBufferDepth * 83 / 10 - 1) % kBufferDepth);
    // Read and finished indices should not be incremented
    BOOST_CHECK_EQUAL(buffer.GetReadIndex(),
                      (kBufferDepth * 83 / 10) % kBufferDepth);
    BOOST_CHECK_EQUAL(buffer.GetFinishedIndex(),
                      (kBufferDepth * 83 / 10 - 1) % kBufferDepth);
  }

  delete[] data;
  data = 0;
}
