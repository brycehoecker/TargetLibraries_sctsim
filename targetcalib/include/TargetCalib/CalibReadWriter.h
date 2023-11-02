// Copyright (c) 2016 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief File access for read / writing Target Module calibration
 */


#pragma clang diagnostic push
#pragma ide diagnostic ignored "OCUnusedMacroInspection"
#ifndef INCLUDE_TARGETCALIB_CALIBREADWRITER_H_
#define INCLUDE_TARGETCALIB_CALIBREADWRITER_H_

#include "TargetCalib/Logger.h"

#include <unistd.h>
#include <iostream>
#include <string>
#include <cstring>
#include <vector>
#include <algorithm>
#include <fitsio.h>
#include <iomanip>
#include <map>
#include <cmath>

#define FILE_TYPE_PED 1 
#define FILE_TYPE_TF 2
#define FILE_TYPE_CF 3
#define FILE_TYPE_TFINPUT 4

// HDU INDEXES USED
#define HDU_CAL 2

// CONSTANTS
#define MAX_PIXELS 65536 // 16-bit, more pixels than this, soemthing went wrong

// ERROR CODES
#define TCAL_FILE_ERR_INPUT         7  //< Inconsistent, invalid data provided
#define TCAL_FILE_ERR_NROWS         6  //< Too many rows
#define TCAL_FILE_ERR_COL           5  //< File column read problem
#define TCAL_FILE_ERR_FORMAT        4  //< File format failure
#define TCAL_FILE_ERR_KEYWORD       3  //< Missing keyword in config file
#define TCAL_FILE_ERR_KEYWORD_TYPE  2  //< Keyword not an int
#define TCAL_FILE_ERR_ACCESS      	1  //< File failure
#define TCAL_FILE_OK                0  //< Success


namespace CTA {
namespace TargetCalib {

/*!
* @class CalibReadWriter
* @brief File access for read / writing Target Module calibration
*
* All data is passed and returned as floating point numbers, 
* compression takes place internally in the file format if specified
* at time of writing, and is read back automatically
*/
class CalibReadWriter {

 public: 

  /*! Default constructor */
  CalibReadWriter() = default;;

  /*! Close file on destruction */
  ~CalibReadWriter() {
    CloseFitsFile();
  }

  /*! Create a fits file and write the header */
  int CreateFitsFile(const std::string& fileName);

  /*! Write the passed header the open file */
  int WriteHeader(std::map<std::string, float> header);

  /*! Calculate the scale and offset to be used in compression based on the
   * range of values in the vector */
  static void CalculateScaleOffset(
    const std::vector<std::vector<std::vector<std::vector<float>>>>& vector,
    uint16_t& scale, int32_t& offset
  );

  /*! Write a vector to the open file */
  int WriteVector(
    const std::vector<std::vector<std::vector<std::vector<float>>>>& vector,
    const std::string& key,
    bool compress, uint16_t scale, int32_t offset
  );

  /*! Write a vector to the open file */
  int WriteVector(
    const std::vector<float>& vector,
    const std::string& key
  );

  /*! Write a vector to the open file */
  int WriteVector(
    const std::vector<int32_t>& vector,
    const std::string& key
  );

  /*! Write Pedestals to a file*/
  int WritePedestalData(
    const std::string& fileName,
    const std::vector<std::vector<std::vector<std::vector<float>>>> &ped,
    const std::vector<std::vector<std::vector<std::vector<float>>>> &hits,
    const std::vector<std::vector<std::vector<std::vector<float>>>> &std,
    bool compress
  );

  /*! Write Pedestals to a file*/
  int WritePedestalData(
    const std::string& fileName,
    const std::vector<std::vector<std::vector<std::vector<float>>>> &ped,
    bool compress=false
  ) {
    std::vector<std::vector<std::vector<std::vector<float>>>> hits;
    std::vector<std::vector<std::vector<std::vector<float>>>> std;
    return WritePedestalData(fileName, ped, hits, std, compress);
  };

  int WriteTfInput(
    const std::string& fileName, const std::vector<float>& amplitudes,
    const std::vector<std::vector<std::vector<std::vector<float>>>> &tf,
    const std::vector<std::vector<std::vector<std::vector<float>>>> &hits
  );

  /*! Write Transfer Functions to a file*/
  int WriteTfData(
    const std::string& fileName, const std::vector<int32_t>& adcSteps,
    const std::vector<std::vector<std::vector<std::vector<float>>>>& tf,
    bool compress=true
  );

  /*! Write Gains to a file*/
  int WriteCfData(std::string fileName,
                  const std::vector<std::vector<float>> &cf,
                  bool compress=true);

  /*! Read Pedestals from file*/
  int ReadPedestalData(
     const std::string& fileName,
     std::vector<std::vector<std::vector<std::vector<float>>>>& ped,
     std::vector<std::vector<std::vector<std::vector<float>>>>& hits,
     std::vector<std::vector<std::vector<std::vector<float>>>>& std
  );

  /*! Read Pedestals from file*/
  int ReadPedestalData(
    const std::string& fileName,
    std::vector<std::vector<std::vector<std::vector<float>>>>& ped
  ) {
    std::vector<std::vector<std::vector<std::vector<float>>>> hits;
    std::vector<std::vector<std::vector<std::vector<float>>>> std;
    return ReadPedestalData(fileName, ped, hits, std);
  };

  /*! Read Gains from file*/
  int ReadCfData(std::string fileName, std::vector<std::vector<float>>& cf);

  int ReadTfInput(
    const std::string& fileName, std::vector<float>& amplitude,
    std::vector<std::vector<std::vector<std::vector<float>>>>& tf,
    std::vector<std::vector<std::vector<std::vector<float>>>> &hits
  );
 
  /*! Read Transfer Functions from file*/
  int ReadTfData(
    const std::string& fileName, std::vector<int32_t>& adcSteps,
    std::vector<std::vector<std::vector<std::vector<float>>>>& tf
  );

 private:

  /*! Global pointer to fits file... can only have one at a time */
  fitsfile* fFitsPointer{};

  /*! Internal function to retrieve the fits error */
  std::string GetFitsError();

  /*! Read a header back from the open file */
  int ReadHeader(std::map<std::string, float>& header,int hdu=1);

  /*! Check that the format of the table is ok - nrows etc */
  int CheckTable(std::map<std::string, float> header, int hdu=2);

  /*! Close the fits file if open */
  int CloseFitsFile();
};

}  // namespace TargetCalib
}  // namespace CTA
#endif  // INCLUDE_TARGETCALIB_CALIBREADWRITER_H_

#pragma clang diagnostic pop
