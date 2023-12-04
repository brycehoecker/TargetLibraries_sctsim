// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#ifndef INCLUDE_TARGETIO_FITSCARDIMAGE_H_
#define INCLUDE_TARGETIO_FITSCARDIMAGE_H_

#include <complex>
#include <string>
#include <cstring>

#include "TargetIO/FitsKeyValue.h"

namespace CTA {
namespace TargetIO {

class FitsCardImage {
 private:
  std::string fComment;
  std::string fKeyword;
  std::shared_ptr<FitsKeyValue> fValue;  // holds card value

  FitsCardImage(const std::string& pKeyword, const char* pValue,
                const std::string& pComment);

 public:
  FitsCardImage(const std::string& pKeyword, const std::string& pComment);
  FitsCardImage(const std::string& pKeyword, const FitsKeyValue& pValue,
                const std::string& pComment);
  FitsCardImage(const std::string& pKeyword, bool pValue,
                const std::string& pComment);
  FitsCardImage(const std::string& pKeyword, double pValue,
                const std::string& pComment);
  FitsCardImage(const std::string& pKeyword, float pValue,
                const std::string& pComment);
  FitsCardImage(const std::string& pKeyword, int32_t pValue,
                const std::string& pComment);
  FitsCardImage(const std::string& pKeyword, int64_t pValue,
                const std::string& pComment);
  FitsCardImage(const std::string& pKeyword, const std::complex<double>& pValue,
                const std::string& pComment);
  FitsCardImage(const std::string& pKeyword, const std::complex<float>& pValue,
                const std::string& pComment);
  FitsCardImage(const std::string& pKeyword, const std::string& pValue,
                const std::string& pComment);
  virtual ~FitsCardImage();

  std::string GetComment() const { return fComment; }
  std::string GetKeyword() const { return fKeyword; }
  std::shared_ptr<FitsKeyValue> GetValue() const { return fValue; }
  bool IsComment() const { return (GetKeyword() == "COMMENT"); }
  bool IsCommentary() const;
  bool IsHistory() const { return (GetKeyword() == "HISTORY"); }
  void Print() const;
  void SetComment(const std::string& pComment) { fComment.assign(pComment); }
  void SetKeyword(const std::string& pKeyword) { fKeyword.assign(pKeyword); }
  void SetEmptyValue();
  void SetValue(const FitsKeyValue& pValue);
  void SetValue(bool pValue);
  void SetValue(double pValue);
  void SetValue(float pValue) { SetValue(static_cast<double>(pValue)); }
  void SetValue(int32_t pValue);
  void SetValue(int64_t pValue);
  void SetValue(const std::complex<double>& pValue);
  void SetValue(const std::complex<float>& pValue) {
    SetValue(std::complex<double>(pValue));
  }
  void SetValue(const std::string& pValue);
  void SetValue(const char* pValue) { SetValue(std::string(pValue)); }
  std::string ToString() const;
};

}  // namespace TargetIO
}  // namespace CTA

#endif  //  INCLUDE_TARGETIO_FITSCARDIMAGE_H_
