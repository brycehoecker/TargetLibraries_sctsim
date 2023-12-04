#ifndef CTA_TARGETCALIB_LOGGER_H_
#define CTA_TARGETCALIB_LOGGER_H_

#include <iostream>
#include <sstream>
#include <string>
#include <stdio.h>
#include <sys/time.h>
#include <fstream>
#include <cstdlib>
#include <bitset>

namespace CTA {
namespace TargetCalib {
  
enum LogLevel { sFatal, sError, sWarning, sInfo, sDebug, sDebugVerbose };
#define FILELOG_MAX_LEVEL sDebugVerbose
 
template <typename T>
class Logger
{
public:
  Logger();
  virtual ~Logger();
  std::ostringstream& Get(const std::string& function, LogLevel level = sInfo);

  static LogLevel& ReportingLevel();
  static std::string ToString(LogLevel level);

protected:
    std::ostringstream os;

 private:
    Logger(const Logger&);
    Logger& operator =(const Logger&);
};

template <typename T>
Logger<T>::Logger()
{
}
 
template <typename T>
  std::ostringstream& Logger<T>::Get(const std::string& function, LogLevel level)
{
   size_t colons = function.find("::");
   size_t begin = function.substr(0,colons).rfind(" ") + 1;
   size_t end = function.rfind("(") - begin;	    
 
  os << __TIMESTAMP__ ;
  os << " [" << function.substr(begin,end) << "]";
  os << ToString(level) << ":";
  os << std::string(level > sDebug ? level - sDebug : 0, ' ');
  return os;
}

template <typename T>
Logger<T>::~Logger()
{
    os << std::endl;
    T::Output(os.str());
}

template <typename T>
LogLevel& Logger<T>::ReportingLevel()
{
    static LogLevel reportingLevel = sDebug;
    return reportingLevel;
}

template <typename T>
std::string Logger<T>::ToString(LogLevel level)
{
  static const char* const buffer[] = {"\033[31m FATAL \033[0m",
				       "\033[91m ERROR \033[0m",
				       "\033[33m WARNING \033[0m",
				       "\033[32m INFO \033[0m",
				       "\033[37m DEBUG \033[0m",
				       "\033[37m DEBUG1 \033[0m"};
  
  return buffer[level];
}

class FileLog
{
public:
    static FILE*& Stream();
    static void Output(const std::string& msg);
};

class FLog : public Logger<FileLog> {};

#define FLOG(function, level)    \
if (level > FILELOG_MAX_LEVEL) ; \
 else if (level > FLog::ReportingLevel() || !FileLog::Stream()) ;	\
 else FLog().Get(function, level) 

#define FLOGOPEN(file)		  \
  FILE* pFile = fopen(file, "a"); \
  FileLog::Stream() = pFile;
#define GDEBUG1  FLOG(__PRETTY_FUNCTION__, sDebugVerbose)
#define GDEBUG   FLOG(__PRETTY_FUNCTION__, sDebug)
#define GINFO    FLOG(__PRETTY_FUNCTION__, sInfo)
#define GWARNING FLOG(__PRETTY_FUNCTION__, sWarning)
#define GERROR   FLOG(__PRETTY_FUNCTION__, sError)
#define GFATAL   FLOG(__PRETTY_FUNCTION__, sFatal)
 
}  // namespace TARGETCALIB
}  // namespace CTA

#endif  // CTA_TARGETCALIB_LOGGER_H_
