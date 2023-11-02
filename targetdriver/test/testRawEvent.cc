// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#define BOOST_TEST_MODULE RAW_EVENT
#include <boost/test/unit_test.hpp>

#include "TargetDriver/RawEvent.h"

BOOST_AUTO_TEST_CASE(TEST_RAW_EVENT) {
  const uint16_t kNPacketsPerEvent = 256;  // = 2048/8
  const uint16_t kPacketSize = 2084;       // 8 waveforms with a 96-ns length
  const double kTimeoutSec = 0.1;

  CTA::TargetDriver::RawEvent event(kNPacketsPerEvent, kPacketSize);
  CTA::TargetDriver::RawEvent::SetTimeoutSec(kTimeoutSec);

  BOOST_CHECK_EQUAL(event.GetTimeoutSec(), kTimeoutSec);
  BOOST_CHECK_EQUAL(event.GetNPacketsPerEvent(), kNPacketsPerEvent);
  BOOST_CHECK_EQUAL(event.GetDataPackets()[0]->GetPacketSize(), kPacketSize);

  BOOST_CHECK_EQUAL(event.IsBeingBuilt(), false);
  BOOST_CHECK_EQUAL(event.IsTimedOut(), false);
  BOOST_CHECK_EQUAL(event.IsComplete(), false);
  BOOST_CHECK_EQUAL(event.WasFlushed(), false);

  uint8_t* data = new uint8_t[kPacketSize];

  for (uint16_t i = 0; i < kNPacketsPerEvent - 1; ++i) {
    event.AddNewPacket(data, i, kPacketSize);
    BOOST_CHECK_EQUAL(event.IsBeingBuilt(), true);
    BOOST_CHECK_EQUAL(event.IsComplete(), false);
  }

  BOOST_CHECK_EQUAL(event.IsTimedOut(), false);
  usleep(static_cast<useconds_t>(kTimeoutSec * 1.2e6));
  BOOST_CHECK_EQUAL(event.IsTimedOut(), true);
  BOOST_CHECK_EQUAL(event.IsComplete(), false);

  BOOST_CHECK_EQUAL(event.WasRead(), false);
  event.SetToRead();
  BOOST_CHECK_EQUAL(event.WasRead(), true);

  delete[] data;
  data = 0;
}
