#ifndef INCLUDE_TARGETDRIVER_RINGBUFFER_H_
#define INCLUDE_TARGETDRIVER_RINGBUFFER_H_

#include <stdint.h>

namespace CTA {
namespace TargetDriver {
class RingBuffer{
private:
  int64_t  fWriteIndex;
  int64_t  fReadIndex;
  int64_t  fBuildIndex;
  int64_t  fSize;

public:
  RingBuffer(int64_t pSize): fWriteIndex(0), fReadIndex(0), fBuildIndex(0) {
    fSize=pSize;
  }
  virtual ~RingBuffer() {}

  inline void Clear() { fWriteIndex=fReadIndex=fBuildIndex=0; }
  inline int64_t GetCapacity() const { return fSize; }
  inline int64_t GetCount() const { return (fSize+fWriteIndex-fReadIndex)%fSize; }
  inline int64_t GetReadIndex() const { return fReadIndex; }
  inline int64_t GetWriteIndex() const { return fWriteIndex; }
  inline int64_t GetBuildIndex() const { return fBuildIndex; }
  inline int64_t NextIndex (int64_t it) const { return (it+1)%fSize; }

  inline bool IsFull() const { return (NextIndex(fWriteIndex)==fReadIndex); }
  inline bool IsEmpty() const { return (fWriteIndex == fReadIndex); }

  inline bool IncWriteIndex() {
    int64_t iNextIndex = NextIndex(fWriteIndex);
    if (iNextIndex == fReadIndex) { return false; }
    fWriteIndex=iNextIndex;
    return true;
  }

  inline bool IncReadIndex() {
    if (IsEmpty()) return false;
    fReadIndex=NextIndex(fReadIndex);
    return true;
  }

  inline bool IncBuildIndex() {
    if (fBuildIndex==fWriteIndex) { return false; }
    fBuildIndex=NextIndex(fBuildIndex);
    return true;
  }

};
}
}

#endif //INCLUDE_TARGETDRIVER_RINGBUFFER_H_
