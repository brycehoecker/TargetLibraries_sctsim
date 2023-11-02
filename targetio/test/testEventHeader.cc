// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include <unistd.h>

#define BOOST_TEST_MODULE EVENT_HEADER
#include <boost/test/unit_test.hpp>

#include "TargetDriver/EventHeader.h"

BOOST_AUTO_TEST_CASE(TEST_EVENT_HEADER) {
  CTA::TargetDriver::EventHeader header;
  BOOST_CHECK_EQUAL(header.GetEventID(), uint32_t(0));
  BOOST_CHECK_EQUAL(header.GetTACK(), uint64_t(0));
  BOOST_CHECK_EQUAL(header.GetNPacketsFilled(), uint16_t(0));
  int64_t sec, nsec;
  header.GetTimeStamp(sec, nsec);
  BOOST_CHECK_EQUAL(sec, 0);
  BOOST_CHECK_EQUAL(nsec, 0);

  header.SetEventID(100);
  BOOST_CHECK_EQUAL(header.GetEventID(), uint32_t(100));
  header.SetTACK(1000);
  BOOST_CHECK_EQUAL(header.GetTACK(), uint64_t(1000));
  header.SetNPacketsFilled(10);
  BOOST_CHECK_EQUAL(header.GetNPacketsFilled(), uint16_t(10));
  for (int i = 0; i < 10; ++i) {
    header.IncrementNPacketsFilled();
  }
  BOOST_CHECK_EQUAL(header.GetNPacketsFilled(), uint16_t(20));

  header.SetTimeStampNow();
  usleep(5000);  // sleep 5 ms
  double dT = header.CalcDeltaTSinceTimeStamp();
  BOOST_CHECK_CLOSE(dT, 5e-3, 20);  // must be consistent in 10%

  header.Init();
  BOOST_CHECK_EQUAL(header.GetEventID(), uint32_t(0));
  BOOST_CHECK_EQUAL(header.GetTACK(), uint64_t(0));
  BOOST_CHECK_EQUAL(header.GetNPacketsFilled(), uint16_t(0));
  header.GetTimeStamp(sec, nsec);
  BOOST_CHECK_EQUAL(sec, 0);
  BOOST_CHECK_EQUAL(nsec, 0);
}
