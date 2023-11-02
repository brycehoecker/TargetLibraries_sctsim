
// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#define BOOST_TEST_MODULE FITS
#include <boost/test/unit_test.hpp>

#include <sys/stat.h>

#include <TargetDriver/RawEvent.h>

#include <limits>
#include <iostream>

#include "TargetIO/EventFileWriter.h"
#include "TargetIO/EventFileReader.h"

struct Fixture {
  Fixture() : FileName("testFITS.fits") {
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

BOOST_FIXTURE_TEST_CASE(TEST_FITS, Fixture) {
  const uint16_t kPacketSize = 8000;
  const uint16_t kNPacketsPerEvent = 100;
  uint8_t* data = new uint8_t[kPacketSize];
  auto event = new CTA::TargetDriver::RawEvent(kNPacketsPerEvent,
                                                             kPacketSize);
  for (uint16_t i = 0; i < kNPacketsPerEvent; ++i) {
    for (uint16_t j = 0; j < kPacketSize; ++j) {
      data[j] = static_cast<uint8_t>((i + j) % 256);  // write dummy data
    }
    event->AddNewPacket(data, i, kPacketSize);
  }
  delete[] data;
  data = 0;

  CTA::TargetIO::EventFileWriter writer(FileName.c_str(), kNPacketsPerEvent,
                                        kPacketSize);
  writer.AddEvent(event);

  // write dummy FITS headers
  const bool kBOOL = true;
  writer.AddCardImage("BOOL", kBOOL, "BOOL comment");
  const double kDOUBLE = std::numeric_limits<double>::max() * 0.99999999;
  writer.AddCardImage("DOUBLE", kDOUBLE, "DOUBLE comment");
  const float kFLOAT = std::numeric_limits<float>::max();
  writer.AddCardImage("FLOAT", kFLOAT, "FLOAT comment");
  const int32_t kINT32 = std::numeric_limits<int32_t>::max();
  writer.AddCardImage("INT32", kINT32, "INT32 comment");
  const int64_t kINT64 = std::numeric_limits<int64_t>::max();
  writer.AddCardImage("INT64", kINT64, "INT64 comment");
  const std::string kSTRING = "string";
  writer.AddCardImage("STRING", kSTRING, "STRING comment");
  const char kCHAR[5] = "char";
  writer.AddCardImage("CHAR", kCHAR, "CHAR comment");

  // write dummy config
  const std::string kConfig = "This is a test string.";
  writer.WriteConfig(kConfig);
  writer.Close();

  CTA::TargetIO::EventFileReader reader(FileName.c_str());

  // check basic numbers
  BOOST_CHECK_EQUAL(reader.GetPacketSize(), kPacketSize);
  BOOST_CHECK_EQUAL(reader.GetNPacketsPerEvent(), kNPacketsPerEvent);
  BOOST_CHECK_EQUAL(reader.GetNEvents(), uint32_t(1));
  BOOST_CHECK_EQUAL(reader.IsOpen(), true);

  // check some FITS headers
  std::shared_ptr<CTA::TargetIO::FitsCardImage> card;
  card = reader["BOOL"];
  BOOST_CHECK_EQUAL(card->GetValue()->AsBool(), kBOOL);
  BOOST_CHECK_EQUAL(card->GetComment(), "BOOL comment");

  card = reader["DOUBLE"];
  BOOST_CHECK_CLOSE(card->GetValue()->AsDouble(), kDOUBLE, 1e-5);
  BOOST_CHECK_EQUAL(card->GetComment(), "DOUBLE comment");

  card = reader["FLOAT"];
  BOOST_CHECK_CLOSE(card->GetValue()->AsDouble(), kFLOAT, 1e-4);
  BOOST_CHECK_EQUAL(card->GetComment(), "FLOAT comment");

  card = reader["INT32"];
  BOOST_CHECK_EQUAL(card->GetValue()->AsInt64(), kINT32);
  BOOST_CHECK_EQUAL(card->GetComment(), "INT32 comment");

  card = reader["INT64"];
  BOOST_CHECK_EQUAL(card->GetValue()->AsInt64(), kINT64);
  BOOST_CHECK_EQUAL(card->GetComment(), "INT64 comment");

  card = reader["STRING"];
  BOOST_CHECK_EQUAL(card->GetValue()->AsString(), kSTRING);
  BOOST_CHECK_EQUAL(card->GetComment(), "STRING comment");

  card = reader["CHAR"];
  BOOST_CHECK_EQUAL(card->GetValue()->AsString(), std::string(kCHAR));
  BOOST_CHECK_EQUAL(card->GetComment(), "CHAR comment");

  // check the observer's name
  card = reader["OBSERVER"];
  BOOST_CHECK_EQUAL(card->GetValue()->AsString(), getenv("USER"));

  // check the host name
  card = reader["HOSTNAME"];
  char hostname[100];
  gethostname(hostname, sizeof(hostname));
  BOOST_CHECK_EQUAL(card->GetValue()->AsString(), hostname);

  // check config string
  std::string configRead;
  reader.ReadConfig(configRead);
  BOOST_CHECK_EQUAL(kConfig, configRead);

  for (uint16_t i = 0; i < kNPacketsPerEvent; ++i) {
    uint8_t* data = reader.GetEventPacket(0, i);
    for (std::size_t j = 0; j < kPacketSize; ++j) {
      BOOST_CHECK_EQUAL(data[j], (i + j) % 256);  // compare with dummy data
    }
  }
}
