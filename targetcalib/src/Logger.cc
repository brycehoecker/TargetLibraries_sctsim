
#include "TargetCalib/Logger.h"

#include <sys/time.h>

namespace CTA {
namespace TargetCalib {

FILE*& FileLog::Stream()
{
    static FILE* pStream = stdout;
    return pStream;
}

void FileLog::Output(const std::string& msg)
{   
    FILE* pStream = Stream();
    if (!pStream)
        return;
    fprintf(pStream, "%s", msg.c_str());
    fflush(pStream);
}
  

}  // namespace TARGETCALIB
}  // namespace CTA
