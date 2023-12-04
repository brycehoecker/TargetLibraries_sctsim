// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include <sys/stat.h>
#include <fitsio.h>

// Need these two lines to use int32_t and int64_t in format
#ifndef __STDC_FORMAT_MACROS
#define __STDC_FORMAT_MACROS
#endif
#include <inttypes.h>

#if defined(__GNUC__) && !defined(__clang__)
#include <regex.h>  // GCC 4.4.7 does not support C++11 <regex>
#include <cstring>
#else
#include <regex>  // NOLINT(build/c++11), Clang and GCC 4.9.0 support <regex>
#endif

#include <cstdlib>

#include "TargetIO/Util.h"

namespace CTA {
namespace TargetIO {
namespace Util {

int32_t CheckFitsValueType(const std::string& value) {
  // Check the value type of a keyword
  // This implementation is based on the FITS Standard
  // "Definition of the Flexible Image Transport System (FITS)" ver. 3.0
  // We do not support any NON-standard values except for lower cases of 'E'
  // and 'D'
  // We do not support int64_t complex because CFITSIO doesn't

  static const char* cBool = "[TF]";         // T or F
  static const char* cLong = "[+-]?[0-9]+";  // e.g. -0129
  static const char* cDouble =
      "[+-]?(\\.[0-9]+|[0-9]+(\\.[0-9]*)?)([dDeE]?[+-]?[0-9]+)?";  // e.g. 3.4
                                                                  // -4.92D-010
  static const char* cComplexDouble =
      "\\( *[+-]?(\\.[0-9]+|[0-9]+(\\.[0-9]*)?)([dDeE]?[+-]?[0-9]+)? *, "
      "*[+-]?(\\.[0-9]+|[0-9]+(\\.[0-9]*)?)([dDeE]?[+-]?[0-9]+)? *\\)";
  static const char* cString = "'([^']*'')*[^']*'";  // e.g. 'FOO'

#if defined(__GNUC__) && !defined(__clang__)
  regex_t reBool, reLong, reDouble, reComplexDouble, reString;
  if (regcomp(&reBool, cBool, REG_EXTENDED) ||
      regcomp(&reLong, cLong, REG_EXTENDED) ||
      regcomp(&reDouble, cDouble, REG_EXTENDED) ||
      regcomp(&reComplexDouble, cComplexDouble, REG_EXTENDED) ||
      regcomp(&reString, cString, REG_EXTENDED)) {
    return -3;
  }
  const size_t kNMatch = 1;
  regmatch_t pmatch[kNMatch];
#else
  static std::regex reBool(cBool);
  static std::regex reLong(cLong);
  static std::regex reDouble(cDouble);
  static std::regex reComplexDouble(cComplexDouble);
  static std::regex reString(cString);
#endif

#if defined(__GNUC__) && !defined(__clang__)
  if (regexec(&reBool, value.c_str(), kNMatch, pmatch, 0) == 0 &&
      pmatch[0].rm_so == 0 && uint32_t(pmatch[0].rm_eo) == value.length()) {
#else
  if (std::regex_match(value, reBool)) {
#endif
    // Check bool
    return TLOGICAL;
#if defined(__GNUC__) && !defined(__clang__)
  } else if (regexec(&reLong, value.c_str(), kNMatch, pmatch, 0) == 0 &&
             pmatch[0].rm_so == 0 &&
             uint32_t(pmatch[0].rm_eo) == value.length()) {
#else
  } else if (std::regex_match(value, reLong)) {
#endif
    // Check long
    int64_t l64;
    int32_t l32;
    sscanf(value.c_str(), "%" PRId64, &l64);
    sscanf(value.c_str(), "%" PRId32, &l32);
    if (l64 == l32) {
      return TINT;
    } else {
      return TLONGLONG;
    }
#if defined(__GNUC__) && !defined(__clang__)
  } else if (regexec(&reDouble, value.c_str(), kNMatch, pmatch, 0) == 0 &&
             pmatch[0].rm_so == 0 &&
             uint32_t(pmatch[0].rm_eo) == value.length()) {
#else
  } else if (std::regex_match(value, reDouble)) {
#endif
    // Check double
    return TDOUBLE;
#if defined(__GNUC__) && !defined(__clang__)
  } else if (regexec(&reComplexDouble, value.c_str(), kNMatch, pmatch, 0) ==
                 0 &&
             pmatch[0].rm_so == 0 &&
             uint32_t(pmatch[0].rm_eo) == value.length()) {
#else
  } else if (std::regex_match(value, reComplexDouble)) {
#endif
    // Check complex double
    return TDBLCOMPLEX;
#if defined(__GNUC__) && !defined(__clang__)
  } else if (regexec(&reString, value.c_str(), kNMatch, pmatch, 0) == 0 &&
             pmatch[0].rm_so == 0 &&
             uint32_t(pmatch[0].rm_eo) == value.length()) {
#else
  } else if (std::regex_match(value, reString)) {
#endif
    // Check string
    return TSTRING;
  }

  // Check empty value for e.g. COMMENT or HISTORY
  if (value == "") {
    return -2;
  }

  return -1;
}

std::string FitsErrorMessage(int status) {
  static char error[100], error2[100];
  fits_get_errstatus(status, error);
  snprintf(error2, sizeof(error2), "(FITSIO: %s)", error);

  return std::string(error2);
}

float GetVersionOfCFITSIO() {
  float version;
  return ffvers(&version);
}

}  // namespace Util
}  // namespace TargetIO
}  // namespace CTA
