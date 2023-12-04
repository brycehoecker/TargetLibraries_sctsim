// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include <iostream>

#include "TargetIO/EventFile.h"
#include "TargetIO/Util.h"

namespace CTA {
namespace TargetIO {

EventFile::EventFile()
    : fFitsPointer(0), fEventHDUNumber(0), fConfigHDUNumber(0) {}

EventFile::~EventFile() { Close(); }

void EventFile::Close() {

  std::cout << "EventFile::Close()" << std::endl;

  if (!IsOpen()) {
    return;
  }

  int status = 0;
  if (fits_close_file(fFitsPointer, &status)) {
    std::cerr << "Cannot close the file " << Util::FitsErrorMessage(status)
              << std::endl;
  } else {
    fFitsPointer = 0;
  }
}

std::shared_ptr<FitsCardImage> EventFile::GetCardImage(
    const std::string& pKeyword) {
  std::shared_ptr<FitsCardImage> null_return;
  if (!IsOpen()) {
    return std::shared_ptr<FitsCardImage>();
  }

  int status = 0;
  int hdutype = IMAGE_HDU;
  // Always read the header of the primary HDU
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << std::endl;
    return null_return;
  }

  char value[FLEN_VALUE], comment[FLEN_COMMENT];
  status = 0;
  if (fits_read_keyword(fFitsPointer, pKeyword.c_str(), value, comment,
                        &status)) {
    std::cerr << "Cannot find the keyword '" << pKeyword << "' "
              << Util::FitsErrorMessage(status) << std::endl;
    return null_return;
  }

  if (pKeyword == "COMMENT" || pKeyword == "HISTORY") {
    return std::make_shared<FitsCardImage>(pKeyword, comment);
  }

  int32_t datatype = Util::CheckFitsValueType(value);
  status = 0;

  if (datatype == TSTRING) {
    char value_s[81];
    if (fits_read_key(fFitsPointer, datatype, pKeyword.c_str(), value_s,
                      comment, &status)) {
      std::cerr << "Cannot read the keyword as string (keyword=" << pKeyword
                << ", value=" << value << ") " << Util::FitsErrorMessage(status)
                << std::endl;
      return null_return;
    } else {
      return std::make_shared<FitsCardImage>(pKeyword, std::string(value_s),
                                             comment);
    }
  } else if (datatype == TLOGICAL) {
    int32_t value_i;
    if (fits_read_key(fFitsPointer, datatype, pKeyword.c_str(), &value_i,
                      comment, &status)) {
      std::cerr << "Cannot read the keyword as logical (keyword=" << pKeyword
                << ", value=" << value << ") " << Util::FitsErrorMessage(status)
                << std::endl;
      return null_return;
    } else {
      return std::make_shared<FitsCardImage>(
          pKeyword, static_cast<bool>(value_i), comment);
    }
  } else if (datatype == TINT || datatype == TLONGLONG) {
    long long tmp;  // NOLINT(runtime/int), CFITSIO type
    if (fits_read_key(fFitsPointer, TLONGLONG, pKeyword.c_str(), &tmp, comment,
                      &status)) {
      if (datatype == TINT) {
        std::cerr << "Cannot read the keyword as long32 (keyword=" << pKeyword
                  << ", value=" << value << ") "
                  << Util::FitsErrorMessage(status) << std::endl;
      } else {
        std::cerr << "Cannot read the keyword as long64 (keyword=" << pKeyword
                  << ", value=" << value << ") "
                  << Util::FitsErrorMessage(status) << std::endl;
      }
      return null_return;
    } else {
      if (datatype == TINT) {
        return std::make_shared<FitsCardImage>(pKeyword, (int32_t)tmp, comment);
      } else {
        return std::make_shared<FitsCardImage>(pKeyword, (int64_t)tmp, comment);
      }
    }
  } else if (datatype == TDOUBLE) {
    double value_d;
    if (fits_read_key(fFitsPointer, datatype, pKeyword.c_str(), &value_d,
                      comment, &status)) {
      std::cerr << "Cannot read the keyword as double (keyword=" << pKeyword
                << ", value=" << value << ") " << Util::FitsErrorMessage(status)
                << std::endl;
      return null_return;
    } else {
      return std::make_shared<FitsCardImage>(pKeyword, value_d, comment);
    }
  } else if (datatype == TDBLCOMPLEX) {
    double value_fd[2];
    if (fits_read_key(fFitsPointer, datatype, pKeyword.c_str(), value_fd,
                      comment, &status)) {
      std::cerr << "Cannot read the keyword as complex double (keyword="
                << pKeyword << ", value=" << value << ") "
                << Util::FitsErrorMessage(status) << std::endl;
      return null_return;
    } else {
      return std::make_shared<FitsCardImage>(
          pKeyword, std::complex<double>(value_fd[0], value_fd[1]), comment);
    }
  } else if (datatype == -2) {
    return std::make_shared<FitsCardImage>(pKeyword, comment);
  } else {
    std::cerr << "Unknown data type was detected (keyword=" << pKeyword
              << ", value=" << value << ", comment=" << comment << ")\n";
    return null_return;
  }
}

long EventFile::GetNrows() {  // NOLINT(runtime/int), CFITSIO type
  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return -1;
  }

  int status = 0;
  int hdutype = BINARY_TBL;
  if (fits_movabs_hdu(fFitsPointer, 2, &hdutype, &status)) {
    std::cerr << "Cannot move to the event HDU "
              << Util::FitsErrorMessage(status) << std::endl;
    return -1;
  }

  status = 0;
  LONGLONG nrows;
  if (fits_get_num_rowsll(fFitsPointer, &nrows, &status)) {
    std::cerr << "Cannot read the number of rows "
              << Util::FitsErrorMessage(status) << std::endl;
    return -1;
  }

  return nrows;
}

std::string EventFile::GetFileName() const {
  if (!IsOpen()) {
    return "";
  }

  return std::string(fFitsPointer->Fptr->filename);
}

void EventFile::PrintHeader() {
  if (!IsOpen()) {
    return;
  }

  int status = 0;
  int hdutype = IMAGE_HDU;
  // Always read the header of the primary HDU
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << std::endl;
    return;
  }

  for (int i = 1;; ++i) {
    char card[80];
    status = 0;
    fits_read_record(fFitsPointer, i, card, &status);
    if (status == 0) {
      printf("%-80s", card);
    } else {
      break;
    }
  }
}

int EventFile::CopyHeaderIntoNewFile(fitsfile *pNewFileFitsPointer) {
   int status = 0;
   int hdutype;
   if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
      std::cerr << "Cannot move to the primary HDU "
                << Util::FitsErrorMessage(status) << "\n";
      return -1;
   }

   status = 0;
   if (fits_copy_hdu(fFitsPointer, pNewFileFitsPointer, 0, &status)) {
      std::cerr << "Cannot copy HDU from r0 file to the new r1 file "
                << Util::FitsErrorMessage(status) << "\n";
      return -1;
   }

   return 0;
}

bool EventFile::HasCardImage(const std::string& pKeyword) {
  if (!IsOpen()) {
    std::cerr << "File is not open\n";
    return false;
  }

  int status = 0;
  int hdutype = IMAGE_HDU;
  // Always read the header of the primary HDU
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    std::cerr << "Cannot move to the primary HDU "
              << Util::FitsErrorMessage(status) << std::endl;
    return false;
  }

  char value[FLEN_VALUE], comment[FLEN_COMMENT];
  status = 0;
  return fits_read_keyword(fFitsPointer, pKeyword.c_str(), value, comment,
                           &status) == 0;
}

}  // namespace TargetIO
}  // namespace CTA
