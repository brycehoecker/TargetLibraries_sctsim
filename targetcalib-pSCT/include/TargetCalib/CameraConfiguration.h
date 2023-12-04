//
// Created by Jason Watson on 06/03/2018.
//

#ifndef TARGETCALIB_CAMERACONFIGURATION_H
#define TARGETCALIB_CAMERACONFIGURATION_H

#include <cstdint>
#include <string>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <iostream>
#include <vector>
#include <cmath>
#include <sstream>
#include "TargetCalib/Logger.h"
#include "TargetCalib/Mapping.h"
#include "TargetCalib/Utils.h"

namespace CTA {
namespace TargetCalib {

struct Version
{
  int major = 0, minor = 0, revision = 0;

  Version(const char* version) {
    std::sscanf(version, "%d.%d.%d", &major, &minor, &revision);
  }

  Version(const std::string &version) : Version(version.c_str()) {}

  operator std::string() const {
    std::ostringstream ss;
    ss << major << '.' << minor << '.' << revision;
    return ss.str();
  }
};

inline std::ostream &operator << (std::ostream &os, const Version& version) {
  return os << version.major << '.' << version.minor << '.' << version.revision;
}

//inline std::string operator std::string(const Version& version) const {
//  std::ostringstream ss;
//  ss << version;
//  return ss.str();
//}

inline bool operator == (const Version& lhs, const Version& rhs)
{
  return lhs.major == rhs.major
         && lhs.minor == rhs.minor
         && lhs.revision == rhs.revision;
}

inline bool operator < (const Version& lhs, const Version& rhs)
{
  if (lhs.major < rhs.major)
    return true;
  if (lhs.major == rhs.major
      && lhs.minor < rhs.minor)
    return true;
  if (lhs.major == rhs.major
      && lhs.minor == rhs.minor
      && lhs.revision < rhs.revision)
    return true;
  return false;
}

inline bool operator > (const Version& lhs, const Version& rhs)
{
  return !(lhs < rhs) && !(lhs == rhs);
}

inline bool operator <= (const Version& lhs, const Version& rhs)
{
  return (lhs < rhs) || (lhs == rhs);
}

inline bool operator >= (const Version& lhs, const Version& rhs)
{
  return (lhs > rhs) || (lhs == rhs);
}


class CameraConfiguration {
private:
  Version fVersion;
  std::string fDescription;
  uint16_t fNCells;
  std::string fMappingPath;
  std::string fReferencePulsePath;

  void SetDescription();
  void SetNCells();
  void SetMapping();
  void SetReferencePulse();

public:
  CameraConfiguration(std::string version="1.1.0");

  std::string GetVersion(){
    return (std::string) fVersion;
  }

  std::string GetDescription() {
    return fDescription;
  }

  uint16_t GetNCells() {
    return fNCells;
  }

  std::string GetMappingPath() {
    return fMappingPath;
  }

  Mapping GetMapping(bool singleModule=false) {
    return Mapping(fMappingPath, singleModule);
  }

  std::string GetReferencePulsePath() {
    return fReferencePulsePath;
  }

  std::vector<std::vector<float>> GetReferencePulse() {
    GINFO << "Loading Reference Pulse Config: " << fReferencePulsePath;
    std::ifstream infile(fReferencePulsePath);
    if (!infile.is_open())
      GERROR << "Cannot find config file: " << fReferencePulsePath;

    std::vector<std::vector<float>> reference_pulse;
    float refx, refy;
    while (infile >> refx >> refy) {
      reference_pulse.push_back({refx, refy});
    }
    infile.close();
    return reference_pulse;
  }

};

}}


#endif //TARGETCALIB_CAMERACONFIGURATION_H
