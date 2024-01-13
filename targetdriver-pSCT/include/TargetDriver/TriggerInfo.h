#ifndef INCLUDE_TARGETDRIVER_TRIGGERINFO_H_
#define INCLUDE_TARGETDRIVER_TRIGGERINFO_H_

#include <sys/time.h>
#include <iostream>
#include <string>

#define TRIGGER_PATTERN_BYTES 64

namespace CTA {
namespace TargetDriver {

/*!
@class TriggerInfo
@brief
*/
class TriggerInfo {
 private:
  uint32_t fEventCount;
  uint16_t fEventType;
  uint64_t fTACK;
  uint8_t fTriggerPattern[TRIGGER_PATTERN_BYTES];
  int64_t fTimeStampSec;      //!< (sec) part of the event time stamp
  int64_t fTimeStampNonoSec;  //!< (ns) part of the event time stamp

 public:
  TriggerInfo()
      : fEventCount(0),
        fEventType(0),
        fTACK(0),
        fTimeStampSec(0),
        fTimeStampNonoSec(0) {
    for (unsigned int i = 0; i < TRIGGER_PATTERN_BYTES; ++i) {
      fTriggerPattern[i] = 0;
    }
  }
  virtual ~TriggerInfo() {}

  void FillFromPacket(uint8_t* data){};
  void Dump(std::ostream os = std::cout){};
  uint32_t GetEventCount() const { return fEventCount; }
  uint64_t GetTACK() const { return fTACK; }
  bool Triggered(uint8_t superpixel_id) {
    if (superpixel_id >= TRIGGER_PATTERN_BYTES) return false;
    return (fTriggerPattern[superpixel_id] > 0);
  }
  void GetTimeStamp(int64_t& pSec,              // NOLINT(runtime/references)
                    int64_t& pNanosec) const {  // NOLINT(runtime/references)
    pSec = fTimeStampSec;
    pNanosec = fTimeStampNonoSec;
  }
  void SetTimeStampNow();
};

/// @brief Set fTimeStamp to the current system time
inline void TriggerInfo::SetTimeStampNow() {
#ifdef __MACH__
  timeval tv;
  gettimeofday(&tv, 0);
  fTimeStampSec = tv.tv_sec;
  fTimeStampNonoSec = tv.tv_usec * 1000;
#else
  timespec ts;
  clock_gettime(CLOCK_REALTIME, &ts);
  fTimeStampSec = ts.tv_sec;
  fTimeStampNonoSec = ts.tv_nsec;
#endif
}

}  // namespace TargetDriver
}  // namespace CTA

#endif  // INCLUDE_TARGETDRIVER_TRIGGERINFO_H_
