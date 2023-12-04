// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#ifndef __STDC_FORMAT_MACROS
#define __STDC_FORMAT_MACROS
#endif
#include <inttypes.h>

#include <fitsio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <ctime>
#include <iostream>

#include "TargetIO/EventFileWriter.h"
#include "TargetIO/Util.h"

namespace CTA {
namespace TargetIO {

EventFileWriter::EventFileWriter(const std::string& pFileName,
                                 uint16_t pNPacketsPerEvent,
                                 uint16_t pPacketSizeInByte) :
  //EventFile(),
  //fWatching(false),
  //fWriting(true),
  //fWatcherSleep(100000 /* us */),
  //fEventsWritten(0),
  //fPacketsWritten(0),
  //fEventBuffer(0) {
  
  EventFile(),
  fThread(),  // Default initialization, thread not started
  fEventBuffer(nullptr),  // Assuming no event buffer initially
  fWatching(false),
  fWriting(true),
  fEventsWritten(0),
  fPacketsWritten(0),
  fWatcherSleep(100000 /* us */) {  
	  
  int status = 0;
  if (fits_create_file(&fFitsPointer, pFileName.c_str(), &status)) {
    std::cerr << "Cannot open " << pFileName.c_str() << " "
              << Util::FitsErrorMessage(status) << "\n";
    // Close(false);
    return;
  }

  // Create an empty image HDU for headers
  status = 0;
  if (fits_create_img(fFitsPointer, 16, 0, 0, &status)) {
    std::cerr << "Cannot create the primary HDU "
              << Util::FitsErrorMessage(status) << "\n";
    Close(false);
    return;
  }

  time_t t;
  time(&t);
  struct tm ptm;
  gmtime_r(&t, &ptm);
  char str[FLEN_VALUE];
  snprintf(str, FLEN_VALUE, "%04d-%02d-%02dT%02d:%02d:%02d", ptm.tm_year + 1900,
           ptm.tm_mon + 1, ptm.tm_mday, ptm.tm_hour, ptm.tm_min, ptm.tm_sec);

  char* env;
  env = getenv("USER");
  AddCardImage("OBSERVER", env != 0 ? env : "", "User name");
  char hostname[BUFSIZ];
  int ret = gethostname(hostname, sizeof(hostname));
  AddCardImage("HOSTNAME", ret >= 0 ? hostname : "", "Host name");
  AddCardImage("DATE-OBS", std::string(str, FLEN_VALUE),
               "Start date and time of the observation (UTC)");

  InitBinaryTable(pNPacketsPerEvent, pPacketSizeInByte);
}//EventFileWriter

EventFileWriter::EventFileWriter(const std::string& pR1FileName,
                                 CTA::TargetIO::EventFileReader* pR0Reader) :
          //EventFile(),
          //fWatching(false),
          //fWriting(true),
          //fWatcherSleep(100000 /* us */),
          //fEventsWritten(0),
          //fPacketsWritten(0),
          //fEventBuffer(0)
          
          EventFile(),
          fThread(),  // Default initialization, thread not started
          fEventBuffer(nullptr),  // Assuming no event buffer initially
          fWatching(false),
          fWriting(true),
          fEventsWritten(0),
          fPacketsWritten(0),
          fWatcherSleep(100000 /* us */)
{
  int status = 0;
  if (fits_create_file(&fFitsPointer, pR1FileName.c_str(), &status)) {
     std::cerr << "Cannot open " << pR1FileName.c_str() << " "
               << Util::FitsErrorMessage(status) << "\n";
     // Close(false);
     return;
  }

  if (pR0Reader->CopyHeaderIntoNewFile(fFitsPointer)) {
    return;
  }

  time_t t;
  time(&t);
  struct tm ptm;
  gmtime_r(&t, &ptm);
  char str[FLEN_VALUE];
  snprintf(str, FLEN_VALUE, "%04d-%02d-%02dT%02d:%02d:%02d", ptm.tm_year + 1900,
         ptm.tm_mon + 1, ptm.tm_mday, ptm.tm_hour, ptm.tm_min, ptm.tm_sec);
  AddCardImage("DATE-CAL", std::string(str, FLEN_VALUE),
            "Start date and time of the r1 calibration (UTC)");

  uint16_t nPacketsPerEvent = (uint16_t) pR0Reader->GetNPacketsPerEvent();
  uint16_t packetSize = pR0Reader->GetPacketSize();
  InitBinaryTable(nPacketsPerEvent, packetSize);
}

void EventFileWriter::AddComment(const std::string& pComment) {
  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return;
  }

  int status = 0;
  int hdutype;
  // Always write in the header of the primary HDU
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << "\n";
    return;
  }

  if (fits_write_comment(fFitsPointer, pComment.c_str(), &status)) {
    std::cerr << "Cannot write the keyword " << Util::FitsErrorMessage(status)
              << "\n";
    return;
  }
}

void EventFileWriter::AddHistory(const std::string& pHistory) {
  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return;
  }

  int status = 0;
  int hdutype;
  // Always write in the header of the primary HDU
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << "\n";
    return;
  }

  if (fits_write_history(fFitsPointer, pHistory.c_str(), &status)) {
    std::cerr << "Cannot write the keyword " << Util::FitsErrorMessage(status)
              << "\n";
    return;
  }
}

void EventFileWriter::AddCardImage(const std::string& pKeyword, bool pValue,
                                   const std::string& pComment, bool pUpdate) {
  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return;
  }

  int status = 0;
  int hdutype;
  // Always write in the header of the primary HDU
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << "\n";
    return;
  }

  if (pUpdate) {
#if ((CFITSIO_MAJOR >= 3) && (CFITSIO_MINOR >= 33))
    if (fits_update_key(fFitsPointer, TLOGICAL, pKeyword.c_str(), &pValue,
                        pComment.c_str(), &status)) {
#else
    if (fits_update_key(fFitsPointer, TLOGICAL, pKeyword.c_str(), &pValue,
                        //static_cast<char*>(pComment.c_str()), &status)) {
						pComment.c_str(), &status)) {	//Bryces Change
#endif
      std::cerr << "Cannot update the keyword "
                << Util::FitsErrorMessage(status) << "\n";
      return;
    }
  } else {
    if (fits_write_key(fFitsPointer, TLOGICAL, pKeyword.c_str(), &pValue,
                       pComment.c_str(), &status)) {
      std::cerr << "Cannot write the keyword " << Util::FitsErrorMessage(status)
                << "\n";
      return;
    }
  }
}

void EventFileWriter::AddCardImage(const std::string& pKeyword, double pValue,
                                   const std::string& pComment, bool pUpdate) {
  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return;
  }

  int status = 0;
  int hdutype;
  // Always write in the header of the primary HDU
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << "\n";
    return;
  }

  if (pUpdate) {
#if ((CFITSIO_MAJOR >= 3) && (CFITSIO_MINOR >= 33))
    if (fits_update_key(fFitsPointer, TDOUBLE, pKeyword.c_str(), &pValue,
                        pComment.c_str(), &status)) {
#else
    if (fits_update_key(fFitsPointer, TDOUBLE, pKeyword.c_str(), &pValue,
                        //static_cast<char*>(pComment.c_str()), &status)) {
						pComment.c_str(), &status)) {
#endif
      std::cerr << "Cannot update the keyword "
                << Util::FitsErrorMessage(status) << "\n";
      return;
    }
  } else {
    if (fits_write_key(fFitsPointer, TDOUBLE, pKeyword.c_str(), &pValue,
                       pComment.c_str(), &status)) {
      std::cerr << "Cannot write the keyword " << Util::FitsErrorMessage(status)
                << "\n";
      return;
    }
  }
}

void EventFileWriter::AddCardImage(const std::string& pKeyword, float pValue,
                                   const std::string& pComment, bool pUpdate) {
  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return;
  }

  int status = 0;
  int hdutype;
  // Always write in the header of the primary HDU
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << "\n";
    return;
  }

  if (pUpdate) {
#if ((CFITSIO_MAJOR >= 3) && (CFITSIO_MINOR >= 33))
    if (fits_update_key(fFitsPointer, TFLOAT, pKeyword.c_str(), &pValue,
                        pComment.c_str(), &status)) {
#else
    if (fits_update_key(fFitsPointer, TFLOAT, pKeyword.c_str(), &pValue,
                        //static_cast<char*>(pComment.c_str()), &status)) {
						pComment.c_str(), &status)) {	//Bryces change
#endif
      std::cerr << "Cannot update the keyword "
                << Util::FitsErrorMessage(status) << "\n";
      return;
    }
  } else {
    if (fits_write_key(fFitsPointer, TFLOAT, pKeyword.c_str(), &pValue,
                       pComment.c_str(), &status)) {
      std::cerr << "Cannot write the keyword " << Util::FitsErrorMessage(status)
                << "\n";
      return;
    }
  }
}

void EventFileWriter::AddCardImage(const std::string& pKeyword, int32_t pValue,
                                   const std::string& pComment, bool pUpdate) {
  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return;
  }

  int status = 0;
  int hdutype;
  // Always write in the header of the primary HDU
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << "\n";
    return;
  }

  if (pUpdate) {
#if ((CFITSIO_MAJOR >= 3) && (CFITSIO_MINOR >= 33))
    if (fits_update_key(fFitsPointer, TINT, pKeyword.c_str(), &pValue,
                        pComment.c_str(), &status)) {
#else
    if (fits_update_key(fFitsPointer, TINT, pKeyword.c_str(), &pValue,
                        //static_cast<char*>(pComment.c_str()), &status)) {
						pComment.c_str(), &status)) {	//Bryces change
#endif
      std::cerr << "Cannot update the keyword "
                << Util::FitsErrorMessage(status) << "\n";
      return;
    }
  } else {
    if (fits_write_key(fFitsPointer, TINT, pKeyword.c_str(), &pValue,
                       pComment.c_str(), &status)) {
      std::cerr << "Cannot write the keyword " << Util::FitsErrorMessage(status)
                << "\n";
      return;
    }
  }
}

void EventFileWriter::AddCardImage(const std::string& pKeyword, int64_t pValue,
                                   const std::string& pComment, bool pUpdate) {
  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return;
  }

  int status = 0;
  int hdutype;
  // Always write in the header of the primary HDU
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << "\n";
    return;
  }

  if (pUpdate) {
#if ((CFITSIO_MAJOR >= 3) && (CFITSIO_MINOR >= 33))
    if (fits_update_key(fFitsPointer, TLONGLONG, pKeyword.c_str(), &pValue,
                        pComment.c_str(), &status)) {
#else
    if (fits_update_key(fFitsPointer, TLONGLONG, pKeyword.c_str(), &pValue,
                        //static_cast<char*>(pComment.c_str()), &status)) {
						pComment.c_str(), &status)) {		//Bryces change
#endif
      std::cerr << "Cannot update the keyword "
                << Util::FitsErrorMessage(status) << "\n";
      return;
    }
  } else {
    if (fits_write_key(fFitsPointer, TLONGLONG, pKeyword.c_str(), &pValue,
                       pComment.c_str(), &status)) {
      std::cerr << "Cannot write the keyword " << Util::FitsErrorMessage(status)
                << "\n";
      return;
    }
  }
}

void EventFileWriter::AddCardImage(const std::string& pKeyword,
                                   const std::string& pValue,
                                   const std::string& pComment, bool pUpdate) {
  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return;
  }

  int status = 0;
  int hdutype;
  // Always write in the header of the primary HDU
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << "\n";
    return;
  }

  char str[FLEN_VALUE];
  snprintf(str, FLEN_VALUE, "%s", pValue.c_str());

  if (pUpdate) {
#if ((CFITSIO_MAJOR >= 3) && (CFITSIO_MINOR >= 33))
    if (fits_update_key(fFitsPointer, TSTRING, pKeyword.c_str(), str,
                        pComment.c_str(), &status)) {
#else
    if (fits_update_key(fFitsPointer, TSTRING, pKeyword.c_str(), str,
                        //static_cast<char*>(pComment.c_str()), &status)) {
						pComment.c_str(), &status)) {		//Bryces Change
#endif
      std::cerr << "Cannot update the keyword "
                << Util::FitsErrorMessage(status) << "\n";
      return;
    }
  } else {
    if (fits_write_key(fFitsPointer, TSTRING, pKeyword.c_str(), str,
                       pComment.c_str(), &status)) {
      std::cerr << "Cannot write the keyword " << Util::FitsErrorMessage(status)
                << "\n";
      return;
    }
  }
}

void EventFileWriter::AddEvent(TargetDriver::RawEvent* pRawEvent) {

  ++fEventsWritten;
  
  if (!fWriting) return;

  if (!IsOpen()) {
    std::cerr << "Cannot AddEvent - file is not open\n";
    return;
  }

  LONGLONG firstrow = GetNrows() + 1;
  LONGLONG firstelem = 1;

  // Event ID
  int status = 0;
  uint64_t eventid = pRawEvent->GetEventHeader().GetEventID();
  
  if (fits_write_col(fFitsPointer, TUINT, 1, firstrow, firstelem, 1,
                     static_cast<void*>(&eventid), &status)) {
    std::cerr << "Cannot write an event packet"
              << Util::FitsErrorMessage(status) << "\n";
    return;
  }

  // TACK
  uint64_t tack = pRawEvent->GetEventHeader().GetTACK();
  uint32_t tack4msb = uint32_t(tack >> 32);
  uint32_t tack4lsb = uint32_t(tack & 0xFFFFFFFF);
  status = 0;
  if (fits_write_col(fFitsPointer, TUINT, 2, firstrow, firstelem, 1,
                     static_cast<void*>(&tack4msb), &status)) {
    std::cerr << "Cannot fill TACK_4MSB" << Util::FitsErrorMessage(status)
              << "\n";
    return;
  }
  status = 0;
  if (fits_write_col(fFitsPointer, TUINT, 3, firstrow, firstelem, 1,
                     static_cast<void*>(&tack4lsb), &status)) {
    std::cerr << "Cannot fill TACK_4LSB" << Util::FitsErrorMessage(status)
              << "\n";
    return;
  }

  // Number of filled packets
  uint16_t npacketsfilled = pRawEvent->GetEventHeader().GetNPacketsFilled();
  status = 0;
  if (fits_write_col(fFitsPointer, TUSHORT, 4, firstrow, firstelem, 1,
                     static_cast<void*>(&npacketsfilled), &status)) {
    std::cerr << "Cannot fill N_PACKETS_FILLED"
              << Util::FitsErrorMessage(status) << "\n";
    return;
  }

  // Time stamp
  int64_t tsec, tnsec;
  pRawEvent->GetEventHeader().GetTimeStamp(tsec, tnsec);
  status = 0;
  if (fits_write_col(fFitsPointer, TLONGLONG, 5, firstrow, firstelem, 1,
                     static_cast<void*>(&tsec), &status)) {
    std::cerr << "Cannot fill TIME_STAMP_SEC" << Util::FitsErrorMessage(status)
              << "\n";
    return;
  }
  status = 0;
  if (fits_write_col(fFitsPointer, TLONGLONG, 6, firstrow, firstelem, 1,
                     static_cast<void*>(&tnsec), &status)) {
    std::cerr << "Cannot fill TIME_STAMP_NSEC" << Util::FitsErrorMessage(status)
              << "\n";
    return;
  }

  std::size_t nheader = CTA::TargetDriver::EventHeader::kColumnForm.size();

  auto packets = pRawEvent->GetDataPackets();
  std::size_t i = 0;
  for (auto it = packets.begin(); it != packets.end(); ++it, ++i) {
    if ((*it)->IsFilled()) {
      LONGLONG nelements = (*it)->GetPacketSize();
      int colnum = static_cast<int>(i + 1 + nheader);
      status = 0;
      if (fits_write_col(fFitsPointer, TBYTE, colnum, firstrow, firstelem,
                         nelements,
                         const_cast<void*>(
                             reinterpret_cast<const void*>((*it)->GetData())),
                         &status)) {
        std::cerr << "Cannot write an event packet"
                  << Util::FitsErrorMessage(status) << "\n";
        return;
      }
      ++fPacketsWritten;
    } else {
      // TODO(Akira): Should something be filled here? zero value array?
    }
  }
}

void EventFileWriter::Close(bool pWriteDateEnd) {

  if (fEventBuffer) { // fEventBuffer is not set when performing r1 calib
    fEventBuffer->Flush();
    usleep(2 * fWatcherSleep);
    StopWatchingBuffer();

    if (IsOpen() && pWriteDateEnd) {
      time_t t;
      time(&t);
      struct tm ptm;
      gmtime_r(&t, &ptm);
      char str[FLEN_VALUE];
      snprintf(str, FLEN_VALUE, "%04d-%02d-%02dT%02d:%02d:%02d",
               ptm.tm_year + 1900, ptm.tm_mon + 1, ptm.tm_mday, ptm.tm_hour,
               ptm.tm_min, ptm.tm_sec);
      AddCardImage("DATE-END", std::string(str),
                   "End date and time of the observation (UTC)");

      std::cout << "EventFileWriter - closing file - wrote "
                << fPacketsWritten << " packets in "
                << fEventsWritten << " events" << std::endl;
    }
  }
  EventFile::Close();
}

void EventFileWriter::Flush() {
  int status;

  if (fWriting) 
    fits_flush_file(fFitsPointer, &status);
}

/// Initializes a binary table in which all event data is saved. This method
/// should be called only once before starting to write event data.
/// @param pNPacketsPerEvent The number of packets per trigger. In normal
/// operation, it is equal to (32 modules) x (N of packets per module). The
/// second factor depends on FPGA settings.
/// @param pPacketSizeInByte The size of a single event packet in bytes. It can
/// be calculated as packetsize = (N of channels per packet) x
/// (N of blocks x 32 x 2 bytes + 2 bytes) + 20 bytes.
void EventFileWriter::InitBinaryTable(uint16_t pNPacketsPerEvent,
                                      uint16_t pPacketSizeInByte) {
  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return;
  }

  // Version 1: Old libCHEC version in which TTYPEs had white spaces, but it is
  // not recommended in the FITS standard
  // Version 2: Replaced white spaces in TTYPEs with underscores
  AddCardImage("EVENT_HEADER_VERSION", (int32_t)2, "");

  std::size_t nheader = CTA::TargetDriver::EventHeader::kColumnForm.size();
  std::size_t nfields = nheader + pNPacketsPerEvent;
  char** ttype = new char* [nfields];
  char** tform = new char* [nfields];
  char** tunit = new char* [nfields];

  for (std::size_t i = 0; i < nheader; ++i) {
    std::size_t ttype_n =
        CTA::TargetDriver::EventHeader::kColumnType[i].size() + 1;
    std::size_t tform_n =
        CTA::TargetDriver::EventHeader::kColumnForm[i].size() + 1;
    std::size_t tunit_n =
        CTA::TargetDriver::EventHeader::kColumnUnit[i].size() + 1;
    ttype[i] = new char[ttype_n];
    tform[i] = new char[tform_n];
    tunit[i] = new char[tunit_n];
    snprintf(ttype[i], ttype_n, "%s",
             CTA::TargetDriver::EventHeader::kColumnType[i].c_str());
    snprintf(tform[i], tform_n, "%s",
             CTA::TargetDriver::EventHeader::kColumnForm[i].c_str());
    snprintf(tunit[i], tunit_n, "%s",
             CTA::TargetDriver::EventHeader::kColumnUnit[i].c_str());
  }

  for (uint16_t i = 0; i < pNPacketsPerEvent; ++i) {
    long long int i2 = i;        // NOLINT(runtime/int), for GCC 4.3
    long long int packetsize2 =  // NOLINT(runtime/int), for GCC 4.3
        pPacketSizeInByte;
    std::size_t ttype_n =
        strlen("EVENT_PACKET_") + std::to_string(i2).length() + 1;
    std::size_t tform_n =
        std::to_string(packetsize2).length() + strlen("B") + 1;
    ttype[i + nheader] = new char[ttype_n];
    tform[i + nheader] = new char[tform_n];
    tunit[i + nheader] = new char[1];
    // Version 1: "EVENT PACKET %d"
    // Version 2: "EVENT_PACKET_%d"
    snprintf(ttype[i + nheader], ttype_n, "EVENT_PACKET_%d", i);
    snprintf(tform[i + nheader], tform_n, "%dB", pPacketSizeInByte);
    tunit[i + nheader][0] = '\0';
  }

  int status = 0;
  const char* extname = "EVENTS";
  if (fits_create_tbl(fFitsPointer, BINARY_TBL, 0, static_cast<int>(nfields),
                      ttype, tform, tunit, extname, &status)) {
    std::cerr << "Cannot create EVENTS HDU " << Util::FitsErrorMessage(status)
              << "\n";
    Close(false);
  }

  status = 0;
  int hdunum;
  fits_get_hdu_num(fFitsPointer, &hdunum);
  fEventHDUNumber = hdunum;

  for (uint32_t i = 0; i < nfields; ++i) {
    delete[] ttype[i];
    delete[] tform[i];
    delete[] tunit[i];
  }

  delete[] ttype;
  delete[] tform;
  delete[] tunit;
}

/*!
@brief Initialize the image HDU for a camera config file.
@param size The length of a character array.
 */
void EventFileWriter::InitConfigImage(uint32_t pSizeInByte) {
  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return;
  }

  int status = 0;
  int bitpix = SBYTE_IMG;
  int naxis = 1;                        // NOLINT(runtime/int), CFITSIO type
  long naxes[1] = {long(pSizeInByte)};  // NOLINT(runtime/int), CFITSIO type

  if (fits_create_img(fFitsPointer, bitpix, naxis, naxes, &status)) {
    std::cerr << "Cannot create CONFIG HDU " << Util::FitsErrorMessage(status)
              << "\n";
    Close(false);
    return;
  }

  status = 0;
  int hdunum;
  fits_get_hdu_num(fFitsPointer, &hdunum);
  fConfigHDUNumber = hdunum;

  status = 0;
  if (fits_write_key(fFitsPointer, TSTRING, "EXTNAME",
                     const_cast<void*>(reinterpret_cast<const void*>("CONFIG")),
                     0, &status)) {
    std::cerr << "Cannot add keyword 'EXTNAME' to the config HDU "
              << Util::FitsErrorMessage(status) << "\n";
    return;
  }
}

void EventFileWriter::StartWatchingBuffer(
    std::shared_ptr<CTA::TargetDriver::EventBuffer> pEventBuffer) {
  fEventBuffer = pEventBuffer;
  fThread = std::thread(&EventFileWriter::Watcher, this);
}

void EventFileWriter::StopWatchingBuffer() {
  fWatching = false;
  if (fThread.joinable()) {
    fThread.join();
  }
}
 
void EventFileWriter::WriteConfig(const std::string& pConfig) {
  uint32_t size = static_cast<uint32_t>(pConfig.length());

  int status = 0;
  int hdutype;
  if (fits_movabs_hdu(fFitsPointer, fConfigHDUNumber, &hdutype, &status)) {
    InitConfigImage(size);
  }

  long long fpixel = 1;        // NOLINT(runtime/int), CFITSIO type
  long long nelements = size;  // NOLINT(runtime/int), CFITSIO type
  status = 0;
  if (fits_write_img(
          fFitsPointer, TSBYTE, fpixel, nelements,
          const_cast<void*>(reinterpret_cast<const void*>(pConfig.c_str())),
          &status)) {
    std::cerr << "Cannot write RunConfigMessage"
              << Util::FitsErrorMessage(status) << "\n";
  }
}

void EventFileWriter::Watcher() {
  
  uint32_t flushed_evs=0;
  uint32_t flushes=0;
  
  fWatching = true;
  while (fWatching) {
    uint32_t nevents = 0;
    // read all available events
    while (TargetDriver::RawEvent* event = fEventBuffer->ReadEvent()) {
      AddEvent(event);
      ++nevents;
    }
    if (nevents > 0) {
      flushed_evs += nevents;
      ++flushes;
      if (flushes == 100) {
	std::cout << "EventFileWriter::Watcher: average number of events flushed in last 100 flushes " << flushed_evs/(float)flushes << "\n";
	flushes = 0;
	flushed_evs = 0;
      }
      Flush();
    }
    usleep(fWatcherSleep);
  }
}

std::shared_ptr<EventFileWriter> EventFileWriter::MakeEventFileWriter(
    const CTA::TargetDriver::DataListener& listener, const std::string& fname) {

  auto buffer = listener.GetEventBuffer();
  uint16_t packetSize = buffer->GetPacketSize();
  uint16_t nPacketsPerEvent = buffer->GetNPacketsPerEvent();
  auto writer = std::make_shared<CTA::TargetIO::EventFileWriter>(
      fname, nPacketsPerEvent, packetSize);
  writer->StartWatchingBuffer(buffer);

  return writer;
}
}  // namespace TargetIO
}  // namespace CTA
