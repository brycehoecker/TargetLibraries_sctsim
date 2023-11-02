// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#ifndef INCLUDE_TARGETIO_EVENTFILE_H_
#define INCLUDE_TARGETIO_EVENTFILE_H_

#include <fitsio.h>

#include <memory>
#include <string>

#include "TargetIO/FitsCardImage.h"

namespace CTA {
namespace TargetIO {

class EventFile {
 private:
 protected:
  fitsfile* fFitsPointer;
  int fEventHDUNumber;
  int fConfigHDUNumber;

 public:
  EventFile();
  virtual ~EventFile();

  void Close();
  bool IsOpen() const { return fFitsPointer ? true : false; }
  std::shared_ptr<FitsCardImage> GetCardImage(const std::string& pKeyword);
  long GetNrows();  // NOLINT(runtime/int), CFITSIO type
  std::string GetFileName() const;
  void PrintHeader();

  std::shared_ptr<FitsCardImage> operator[](const std::string& pKeyword) {
    return GetCardImage(pKeyword);
  }

  int CopyHeaderIntoNewFile(fitsfile* pNewFileFitsPointer);
  bool HasCardImage(const std::string& pKeyword);

  };

}  // namespace TargetIO
}  // namespace CTA

#endif  // INCLUDE_TARGETIO_EVENTFILE_H_
