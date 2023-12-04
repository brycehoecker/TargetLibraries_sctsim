// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#ifndef __STDC_FORMAT_MACROS
#define __STDC_FORMAT_MACROS 1
#endif
#include <inttypes.h>

#include <iostream>
#include <sstream>
#include <set>

#include "TargetIO/FitsKeyValue.h"
#include "TargetIO/EventFileReader.h"
#include "TargetIO/Util.h"

namespace CTA {
namespace TargetIO {

EventFileReader::EventFileReader(const std::string& pFileName)
    : EventFile(),
      fPacketSize(0),
      fData(0),
      fNEventHeaders(0),
      fEventHeaderVersion(0),
      fNPacketsPerEvent(0) {
  int status = 0;
  if (fits_open_file(&fFitsPointer, pFileName.c_str(), READONLY, &status)) {
    std::cerr << "Cannot open " << pFileName << " "
              << Util::FitsErrorMessage(status);
    Close();
    return;
  }

  std::shared_ptr<FitsCardImage> card = GetCardImage("EVENT_HEADER_VERSION");
  if (card) {
    fEventHeaderVersion = card->GetValue()->AsInt();
  } else {
    fEventHeaderVersion = 0;
  }

  status = 0;
  int hdutype;
  if (fits_movabs_hdu(fFitsPointer, 2, &hdutype, &status) == 0 &&
      hdutype == IMAGE_HDU) {
    fConfigHDUNumber = 2;
  } else {
    status = 0;
    if (fits_movabs_hdu(fFitsPointer, 3, &hdutype, &status) == 0 &&
        hdutype == IMAGE_HDU) {
      fConfigHDUNumber = 3;
    }
  }

  status = 0;
  if (fits_movabs_hdu(fFitsPointer, 2, &hdutype, &status) == 0 &&
      hdutype == BINARY_TBL) {
    fEventHDUNumber = 2;
  } else {
    status = 0;
    if (fits_movabs_hdu(fFitsPointer, 3, &hdutype, &status) == 0 &&
        hdutype == BINARY_TBL) {
      fEventHDUNumber = 3;
    } else {
      std::cerr << "Cannot move to the event HDU "
                << Util::FitsErrorMessage(status);
      Close();
      return;
    }
  }

  long tfields;  // NOLINT(runtime/int), CFITSIO type
  char comment[FLEN_COMMENT];
  if (fits_read_key_lng(fFitsPointer, "TFIELDS", &tfields, comment, &status)) {
    std::cerr << "Cannot read TFIELDS " << Util::FitsErrorMessage(status);
    Close();
    return;
  }

  char value[FLEN_VALUE];
  char tform[FLEN_KEYWORD];

  for (int64_t i = 0; i < tfields && i < 256; ++i) {
    snprintf(tform, FLEN_KEYWORD, "TTYPE%" PRIi64, i + 1);
    if (fits_read_key_str(fFitsPointer, tform, value, comment, &status)) {
      std::cerr << "Cannot read TTYPE" << i + 1 << " "
                << Util::FitsErrorMessage(status);
      Close();
      return;
    } else {
      // found the first packet column
      if (strcmp(value, "EVENT PACKET 0") == 0 ||
          strcmp(value, "EVENT_PACKET_0") == 0) {  // for new version
        fNEventHeaders = static_cast<uint8_t>(i);
        break;
      }
    }
  }

  fNPacketsPerEvent = static_cast<uint32_t>(tfields - fNEventHeaders);

  for (int i = fNEventHeaders; i < tfields; ++i) {
    snprintf(tform, FLEN_KEYWORD, "TFORM%d", i + 1);
    if (fits_read_key_str(fFitsPointer, tform, value, comment, &status)) {
      std::cerr << "Cannot read TFORM" << i + 1 << " "
                << Util::FitsErrorMessage(status) << std::endl;
      Close();
      return;
    }

    uint16_t packet_size;
    if (sscanf(value, "%" SCNu16 "B", &packet_size) == 1) {
      if (i > fNEventHeaders && packet_size != fPacketSize) {
        std::cerr << "Expected value of TFORM" << i << " is " << fPacketSize
                  << "B, but it is " << value << std::endl;
        Close();
      }
      if (fData == 0) {
        fPacketSize = packet_size;
        fData = new uint8_t[fPacketSize];
      }
    } else {
      fPacketSize = 0;
      std::cerr << "Expected value of TFORM" << i << " is xxxB, but it is "
                << value << std::endl;
      Close();
    }
  }
}

EventFileReader::~EventFileReader() {
  Close();
  delete[] fData;
  fData = 0;
}

void EventFileReader::Close() {
  EventFile::Close();
  fPacketSize = 0;
}

bool EventFileReader::GetEventHeaderFast(
    uint32_t pEventIndex, CTA::TargetDriver::EventHeader& pHeader) {
  /// Note: fits_movabs_hdu will not be called for speed up
  int status = 0;

  // don't change the type used in CFITSIO
  long nelements = 1;  // NOLINT(runtime/int), CFITSIO type
  long firstelem = 1;  // NOLINT(runtime/int), CFITSIO type

  if (fEventHeaderVersion == 0) {
    uint32_t eventid;
    fits_read_col(fFitsPointer, TUINT, 1, pEventIndex + 1, firstelem, nelements,
                  0, &eventid, 0, &status);
    if (status == 0) {
      pHeader.SetEventID(eventid);
    }

    uint32_t tack[2];
    status = 0;
    fits_read_col(fFitsPointer, TUINT, 2, pEventIndex + 1, firstelem, 2, 0,
                  &tack, 0, &status);
    if (status == 0) {
      uint64_t tack2 = (uint64_t(tack[0]) << 32) | tack[1];
      pHeader.SetTACK(tack2);
    }

    uint16_t npacketsfilled;
    status = 0;
    fits_read_col(fFitsPointer, TUSHORT, 3, pEventIndex + 1, firstelem,
                  nelements, 0, &npacketsfilled, 0, &status);
    if (status == 0) {
      pHeader.SetNPacketsFilled(npacketsfilled);
    } else {
      std::cerr << "Cannot read N_PACKETS_FILLED from " << pEventIndex
                << "dth event in" << GetFileName() << ": "
                << Util::FitsErrorMessage(status);
    }

    int64_t t[2];
    status = 0;
    fits_read_col(fFitsPointer, TLONGLONG, 4, pEventIndex + 1, firstelem, 2, 0,
                  &t, 0, &status);
    if (status == 0) {
      pHeader.SetTimeStamp(t[0], t[1]);
    }
  } else if (fEventHeaderVersion == 1 || fEventHeaderVersion == 2) { //TODO: HACK to fix for fEventHeaderVersion == 2 (JASON)
    uint32_t eventid;
    fits_read_col(fFitsPointer, TUINT, 1, pEventIndex + 1, firstelem, nelements,
                  0, &eventid, 0, &status);
    if (status == 0) {
      pHeader.SetEventID(eventid);
    }

    uint32_t tack32msb, tack32lsb;
    status = 0;
    fits_read_col(fFitsPointer, TUINT, 2, pEventIndex + 1, firstelem, nelements,
                  0, &tack32msb, 0, &status);
    fits_read_col(fFitsPointer, TUINT, 3, pEventIndex + 1, firstelem, nelements,
                  0, &tack32lsb, 0, &status);
    if (status == 0) {
      uint64_t tack = (uint64_t(tack32msb) << 32) | tack32lsb;
      pHeader.SetTACK(tack);
    }

    uint16_t npacketsfilled;
    status = 0;
    fits_read_col(fFitsPointer, TUSHORT, 4, pEventIndex + 1, firstelem,
                  nelements, 0, &npacketsfilled, 0, &status);
    if (status == 0) {
      pHeader.SetNPacketsFilled(npacketsfilled);
    } else {
      std::cerr << "Cannot read N_PACKETS_FILLED from " << pEventIndex
                << "dth event in " << GetFileName() << ": "
                << Util::FitsErrorMessage(status);
    }

    int64_t tsec, tnsec;
    status = 0;
    fits_read_col(fFitsPointer, TLONGLONG, 5, pEventIndex + 1, firstelem,
                  nelements, 0, &tsec, 0, &status);
    fits_read_col(fFitsPointer, TLONGLONG, 6, pEventIndex + 1, firstelem,
                  nelements, 0, &tnsec, 0, &status);
    if (status == 0) {
      pHeader.SetTimeStamp(tsec, tnsec);
    }
  }
  return true;
}

bool EventFileReader::GetEventHeader(uint32_t pEventIndex,
                                     CTA::TargetDriver::EventHeader& pHeader) {
  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return false;
  }

  int status = 0;
  int hdutype = BINARY_TBL;
  if (fits_movabs_hdu(fFitsPointer, fEventHDUNumber, &hdutype, &status)) {
    std::cerr << "Cannot move to the event HDU "
              << Util::FitsErrorMessage(status);
    return false;
  }

  return GetEventHeaderFast(pEventIndex, pHeader);
}

uint8_t* EventFileReader::GetEventPacket(uint32_t pEventIndex,
                                         uint16_t pPacketID) {
  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return 0;
  }

  int status = 0;
  int hdutype = BINARY_TBL;
  if (fits_movabs_hdu(fFitsPointer, fEventHDUNumber, &hdutype, &status)) {
    std::cerr << "Cannot move to the event HDU "
              << Util::FitsErrorMessage(status);
    return 0;
  }

  status = 0;
  int anynull;
  if (fits_read_col(fFitsPointer, TBYTE, pPacketID + fNEventHeaders + 1,
                    pEventIndex + 1, 1, fPacketSize, 0, fData, &anynull,
                    &status)) {
    std::cerr << "Cannot read the " << (uint64_t)pPacketID << "th packet of "
              << "the " << pEventIndex << "th event "
              << Util::FitsErrorMessage(status);
    return 0;
  }

  return fData;
}

/*!
@brief Read the config file that was used when taking this run.
 */
void EventFileReader::ReadConfig(std::string& pConfig) {
  int status = 0;
  int hdutype;
  if (fits_movabs_hdu(fFitsPointer, fConfigHDUNumber, &hdutype, &status)) {
    std::cerr << "Cannot move to the config HDU "
              << Util::FitsErrorMessage(status);
    return;
  }

  status = 0;
  char value[FLEN_VALUE];
  if (fits_read_key(fFitsPointer, TSTRING, "NAXIS1", value, 0, &status)) {
    std::cerr << "Cannot read NAXIS1 from the config HDU "
              << Util::FitsErrorMessage(status);
    return;
  }

  status = 0;
  int fpixel = 1;
  int size = atoi(value);
  if (size <= 0 || errno != 0) {
    std::cerr << "Cannot parse NAXIS1 (" << value << ") in the config HDU.\n";
    return;
  }

  char* str = new char[size];
  if (fits_read_img(fFitsPointer, TSBYTE, fpixel, size, 0, str, 0, &status)) {
    std::cerr << "Cannot read config data from the config HDU "
              << Util::FitsErrorMessage(status);
    delete[] str;
    str = 0;
    return;
  }

  pConfig.assign(str, static_cast<std::size_t>(size));

  delete[] str;
  str = 0;
}

int16_t EventFileReader::GetSN(uint16_t slot) {
  int16_t value = -2;

  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return value;
  }

  int status = 0;
  int hdutype;
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << "\n";
    return value;
  }

  int16_t temp_val;
  //char text[11];	
  char text[15];		//Bryces Change
  sprintf(text, "SLOT-%02d-SN", slot);
  char comment[50] = "module serial number";
  if (fits_read_key(fFitsPointer, TINT, text, &temp_val, comment, &status)) {
    return value;
  }
  value = temp_val;

  return value;
}

float EventFileReader::GetSiPMTemp(uint16_t slot) {
  float value = -2;

  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return value;
  }

  int status = 0;
  int hdutype;
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << "\n";
    return value;
  }

  float temp_val;
  char text[20];
  sprintf(text, "SLOT-%02d-TSIPM", slot);
  char comment[50] = "SiPM Temperature";
  if (fits_read_key(fFitsPointer, TFLOAT, text, &temp_val, comment, &status)) {
    return value;
  }
  value = temp_val;

  return value;
}

float EventFileReader::GetPrimaryTemp(uint16_t slot) {
  float value = -2;

  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return value;
  }

  int status = 0;
  int hdutype;
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << "\n";
    return value;
  }

  float temp_val;
  char text[20];
  sprintf(text, "SLOT-%02d-TPRI", slot);
  char comment[50] = "Primary Board Temperature";
  if (fits_read_key(fFitsPointer, TFLOAT, text, &temp_val, comment, &status)) {
    return value;
  }
  value = temp_val;

  return value;
}

int16_t EventFileReader::GetSPDAC(uint16_t slot, uint16_t sp) {
  int16_t value = -2;

  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return value;
  }

  int status = 0;
  int hdutype;
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << "\n";
    return value;
  }

  int16_t temp_val;
  //char text[20];
  char text[25];		//Bryces Change
  sprintf(text, "SLOT-%02d-SP-%02d-DAC", slot, sp);
  char comment[50] = "DAC Setting";
  if (fits_read_key(fFitsPointer, TINT, text, &temp_val, comment, &status)) {
    return value;
  }
  value = temp_val;

  return value;
}

int16_t EventFileReader::GetSPHVON(uint16_t slot, uint16_t sp) {
  int16_t value = -2;

  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return value;
  }

  int status = 0;
  int hdutype;
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << "\n";
    return value;
  }

  int16_t temp_val;
  //char text[20];
  char text[26];		//Bryces Change
  sprintf(text, "SLOT-%02d-SP-%02d-HVON", slot, sp);
  char comment[50] = "HV On/Off";
  if (fits_read_key(fFitsPointer, TINT, text, &temp_val, comment, &status)) {
    return value;
  }
  value = temp_val;

  return value;
}

std::string EventFileReader::GetCameraVersion() {
  std::string camera_version = "1.1.0"; // Default = CHEC-S
  if (HasCardImage("CAMERAVERSION")) {
    camera_version = GetCardImage("CAMERAVERSION")->GetValue()->AsString();
  }
  return camera_version;
}

}  // namespace TargetIO
}  // namespace CTA
