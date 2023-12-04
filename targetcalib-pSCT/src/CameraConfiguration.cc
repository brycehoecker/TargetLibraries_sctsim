//
// Created by Jason Watson on 12/11/2017.
//

#include "TargetCalib/CameraConfiguration.h"

namespace CTA {
namespace TargetCalib {

CameraConfiguration::CameraConfiguration(std::string version)
  : fVersion(Version(version))
{
  if (fVersion == "1.0.1") {
    GINFO << "Camera version 1.0.1 is aliased to 1.1.0";
    fVersion = Version("1.1.0");
  }

  SetDescription();
  SetNCells();
  SetMapping();
  SetReferencePulse();

  GINFO << "Camera Configuration Loaded: V" << fVersion << ", " << fDescription;
}

void CameraConfiguration::SetDescription(){
  if (fVersion == "1.0.0")
    fDescription = "CHEC-M";
  else if ("1.1.0" <= fVersion && fVersion < "2.0.0")
    fDescription = "CHEC-S";
  else
    GERROR << "No SetDescription case for camera version: " << fVersion;
}

void CameraConfiguration::SetNCells() {
  if (fVersion == "1.0.0")
    fNCells = (uint16_t) pow(2, 14);
  else if ("1.1.0" <= fVersion && fVersion < "2.0.0")
    fNCells = (uint16_t) pow(2, 12);
  else
    GERROR << "No SetNCells case for camera version: " << fVersion;
}

void CameraConfiguration::SetMapping() {
  std::string basePath = GetEnv("CONDA_PREFIX") + "/share/TargetCalib/dev/";
  if (fVersion == "1.0.0")
    fMappingPath = basePath + "mapping_checm_V1-0-0.cfg";
  else if ("1.1.0" <= fVersion && fVersion < "2.0.0")
    fMappingPath = basePath + "mapping_checs_V1-1-0.cfg";
  else
    GERROR << "No SetMapping case for camera version: " << fVersion;
}

void CameraConfiguration::SetReferencePulse() {
  std::string basePath = GetEnv("CONDA_PREFIX") + "/share/TargetCalib/dev/";
  if (fVersion == "1.0.0")
    fReferencePulsePath = basePath + "reference_pulse_checm_V1-0-0.cfg";
  else if ("1.1.0" <= fVersion && fVersion < "2.0.0")
    fReferencePulsePath = basePath + "reference_pulse_checs_V1-1-0.cfg";
  else
    GERROR << "No SetMapping case for camera version: " << fVersion;
}


}}