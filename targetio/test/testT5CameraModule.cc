// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#define BOOST_TEST_MODULE T5_CAMERA_MODULE
#include <boost/test/unit_test.hpp>
#include <boost/test/floating_point_comparison.hpp>

#include <sys/stat.h>

#include <TargetDriver/DataListener.h>
#include <TargetDriver/TesterBoard.h>
#include <TargetDriver/TargetModule.h>

#include "TargetIO/EventFileWriter.h"

struct Fixture {
  Fixture() : FileName("testT5CameraModule.fits") {
    if (Exists()) Delete();
  }

  // ~Fixture() { Delete(); }

  bool Exists() {
    struct stat buffer;
    return (stat(FileName.c_str(), &buffer) == 0);
  }

  void Delete() { system(("rm " + FileName).c_str()); }

  std::string FileName;
};

BOOST_FIXTURE_TEST_CASE(TEST_T5_CAMERA_MODULE, Fixture) {
  const uint16_t kNPacketsPerEvent = 16;
  const uint16_t kPacketSize = 1052;  // 4 waveforms with a 128-ns length
  const uint32_t kBufferDepth = 1000;
  const double kTimeoutSec = 0.1;

  const std::string kMyIP = "0.0.0.0";
  const std::string kModuleIP = "192.168.0.85";
  const std::string kTesterIP = "192.168.1.173";

  CTA::TargetDriver::RawEvent::SetTimeoutSec(kTimeoutSec);

  CTA::TargetDriver::TargetModule module(
      "config/TM5_FPGA_Firmware0xFEDA003C.def", "config/TM5_ASIC.def", 0);
  module.EstablishSlowControlLink(kMyIP, kModuleIP);
  // TODO(Akira) Find a good way to reduce this confusion
  module.WriteSetting("NumberOfBlocks", 3);  // 3 + 1 = 4 blocks
  module.WriteSetting("MaxChannelsInPacket", 4);
  // TODO(Akria) This doesn't work on Mac
  // Akira's hack to open fire wall.
  CTA::TargetDriver::TargetModule::DataPortPing(kMyIP, kModuleIP);

  CTA::TargetDriver::DataListener listener(kBufferDepth, kNPacketsPerEvent,
                                           kPacketSize);
  BOOST_CHECK_EQUAL(listener.AddDAQListener(kMyIP), TC_OK);
  listener.StartListening();

  auto writer = CTA::TargetIO::EventFileWriter::MakeEventFileWriter(
      listener, "testT5CameraModule.fits");

  CTA::TargetDriver::TesterBoard tester;
  tester.Init(kMyIP, kTesterIP);

  for (uint32_t i = 0; i < 1000; ++i) {
    tester.SendSoftwareTrigger();
  }

  sleep(1);

  writer->StopWatchingBuffer();

  auto buffer = listener.GetEventBuffer();

  for (uint32_t i = 0; i < 1000; ++i) {
    tester.SendSoftwareTrigger();
    while (true) {
      auto event = buffer->ReadEvent();
      if (event) {
        writer->AddEvent(event);
        break;
      }
    }
  }
}
