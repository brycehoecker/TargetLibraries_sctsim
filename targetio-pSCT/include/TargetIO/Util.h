// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#ifndef INCLUDE_TARGETIO_UTIL_H_
#define INCLUDE_TARGETIO_UTIL_H_

#include <string>

// Error code

namespace CTA {
namespace TargetIO {

/**
 * @brief A namespace for utility functions
 *
 * All utility functions should be declared and defined inside this namespace
 * instead of being naked, so that users can easily distinguish them from those
 * in other libraries.
 */

namespace Util {

int32_t CheckFitsValueType(const std::string& pValue);
std::string FitsErrorMessage(int pStatus);
float GetVersionOfCFITSIO();

}  // namespace Util
}  // namespace TargetIO
}  // namespace CTA

#endif  // INCLUDE_TARGETIO_UTIL_H_
