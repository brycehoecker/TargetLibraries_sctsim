// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#define BOOST_TEST_MODULE EVENT_FILE
#include <boost/test/unit_test.hpp>
#include <boost/test/floating_point_comparison.hpp>
#include <boost/timer.hpp>

#include <sys/stat.h>

#include <TargetDriver/DataListener.h>
#include <TargetDriver/ModuleSimulator.h>

#include <thread>  // NOLINT(build/c++11), <thread> is supported by GCC 4.4.7

#include "TargetIO/EventFileWriter.h"

const uint8_t kNWavesPerPacket = 8;
const uint8_t kNSamplesPerWave = 128;

struct Fixture {
  Fixture() : FileName("testEventFile.fits") {
    if (Exists()) Delete();
  }

  ~Fixture() { Delete(); }

  bool Exists() {
    struct stat buffer;
    return (stat(FileName.c_str(), &buffer) == 0);
  }

  void Delete() { system(("rm " + FileName).c_str()); }

  std::string FileName;
};

int SendDataPacket(CTA::TargetDriver::ModuleSimulator& simulator,  // NOLINT
                   CTA::TargetDriver::DataPacket& packet,         // NOLINT
                   uint32_t eventID, uint16_t packetID) {
  uint64_t tack = eventID;

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

  return simulator.SendDataPacket(packet.GetData(), packet.GetPacketSize());
}

BOOST_FIXTURE_TEST_CASE(TEST_EVENT_FILE_WRITER_SPEED, Fixture) {
  const uint16_t kNPacketsPerEvent = 256;  // = 2048/8
  const uint16_t kPacketSize = 2084;       // 8 waveforms with a 128-ns length
  const uint32_t kBufferDepth = 1000;
  const uint16_t kTriggerRate = 600;  // (Hz)
  const double kTimeoutSec = 0.1;

  std::shared_ptr<CTA::TargetDriver::RawEvent> nullEvent;

  CTA::TargetDriver::RawEvent::SetTimeoutSec(kTimeoutSec);

  CTA::TargetDriver::DataPacket packet(kNWavesPerPacket, kNSamplesPerWave);

  CTA::TargetDriver::ModuleSimulator simulator("0.0.0.0");
  simulator.Start();

  // TODO(Akira): Replace the absolute paths with relative paths
  CTA::TargetDriver::TargetModule module(
      "config/TM5_FPGA_Firmware0xFEDA003C.def", "config/TM5_ASIC.def", 0);
  module.EstablishSlowControlLink("0.0.0.0", "0.0.0.0");

  CTA::TargetDriver::DataListener listener(kBufferDepth, kNPacketsPerEvent,
                                           kPacketSize);
  listener.AddDAQListener("0.0.0.0");
  listener.StartListening();

  CTA::TargetIO::EventFileWriter writer("testEventFile.fits", kNPacketsPerEvent,
                                        kPacketSize);

  auto buffer = listener.GetEventBuffer();

  uint32_t eventID = 0;
  for (uint16_t packetID = 0; packetID < kNPacketsPerEvent; ++packetID) {
    SendDataPacket(simulator, packet, eventID, packetID);
  }
  usleep(100000);
  auto event = buffer->ReadEvent();

  boost::timer t;
  for (uint32_t i = 0; i < 10000; i++) {
    writer.AddEvent(event);
    if (i % 100 == 99) writer.Flush();
  }
  double elapsed = t.elapsed();
  std::cerr << "Elapsed time: " << elapsed << " (sec)\n";
  // must be faster than 600 Hz
  BOOST_CHECK_SMALL(elapsed,
                    writer.GetNrows() / static_cast<double>(kTriggerRate));
  writer.Close();
  listener.StopListening();
}

BOOST_FIXTURE_TEST_CASE(TEST_EVENT_FILE_WRITER, Fixture) {
  const uint16_t kNPacketsPerEvent = 256;  // = 2048/8
  const uint16_t kPacketSize = 2084;       // 8 waveforms with a 128-ns length
  const uint32_t kBufferDepth = 1000;
  const uint16_t kTriggerRate = 200;                      // (Hz)
  const uint16_t kTriggerSleep = 1000000 / kTriggerRate;  // (us)
  const double kTimeoutSec = 0.1;

  std::shared_ptr<CTA::TargetDriver::RawEvent> nullEvent;

  CTA::TargetDriver::RawEvent::SetTimeoutSec(kTimeoutSec);

  CTA::TargetDriver::DataPacket packet(kNWavesPerPacket, kNSamplesPerWave);

  CTA::TargetDriver::ModuleSimulator simulator("0.0.0.0");
  simulator.Start();

  // TODO(Akira): Replace the absolute paths with relative paths
  CTA::TargetDriver::TargetModule module(
      "config/TM5_FPGA_Firmware0xFEDA003C.def", "config/TM5_ASIC.def", 0);
  module.EstablishSlowControlLink("0.0.0.0", "0.0.0.0");

  CTA::TargetDriver::DataListener listener(kBufferDepth, kNPacketsPerEvent,
                                       kPacketSize);
  listener.AddDAQListener("0.0.0.0");
  listener.StartListening();

  CTA::TargetIO::EventFileWriter writer("testEventFile.fits", kNPacketsPerEvent,
                                        kPacketSize);

  auto buffer = listener.GetEventBuffer();
  writer.StartWatchingBuffer(buffer);

  for (uint32_t eventID = 0; eventID < kBufferDepth * 10; ++eventID) {
    for (uint16_t packetID = 0; packetID < kNPacketsPerEvent; ++packetID) {
      // Make packet loss happen
      if (eventID % 1111 == 0 && packetID == 33) {
        continue;
      } else {
        SendDataPacket(simulator, packet, eventID, packetID);
      }
    }
    usleep(kTriggerSleep);
  }

  buffer->Flush();
}
