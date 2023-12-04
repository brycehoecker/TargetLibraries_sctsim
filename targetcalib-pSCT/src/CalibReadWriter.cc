// Copyright (c) 2016 The CTA Consortium. All rights reserved.
#include "TargetCalib/CalibReadWriter.h"


namespace CTA {
namespace TargetCalib {


int CalibReadWriter::CreateFitsFile(const std::string& fileName){

  int status = 0;
        
  // Create output file
  GDEBUG1 << "Creating new fits file: " << fileName;
  std::string newFileName = "!";
  newFileName.append(fileName);
  if (fits_create_file(&fFitsPointer, newFileName.c_str(), &status)) {
    GERROR << "Cannot open " << fileName.c_str() << " " << GetFitsError();
    CloseFitsFile();
    return TCAL_FILE_ERR_ACCESS;
  }
  
  // Setup an empty image HDU for headers
  GDEBUG1 << "Creating header HDU";
  status = 0;
  if (fits_create_img(fFitsPointer, 16, 0, nullptr, &status)) {
    GERROR << "Cannot create the primary HDU " << GetFitsError();
    CloseFitsFile();
    return TCAL_FILE_ERR_ACCESS;
  }
        
  return TCAL_FILE_OK;
}

int CalibReadWriter::WriteHeader(std::map<std::string, float> header){

  if (!fFitsPointer) return TCAL_FILE_ERR_ACCESS;

  int status = 0;
  int hdutype;
  GDEBUG1 << "Moving to header HDU";
  if (fits_movabs_hdu(fFitsPointer, 1, &hdutype, &status)) {
    GERROR << "Cannot move to the header HDU, " << GetFitsError();
    return TCAL_FILE_ERR_FORMAT;
  }
  status = 0;
  GDEBUG1 << "Writing header key, value pairs";
  for (auto &key : header) {
    if (fits_write_key(fFitsPointer, TFLOAT, key.first.c_str(),
                       &key.second, "", &status)) {
      GERROR << "Cannot write the keyword to header (keyword=" << key.first
             << ", value=" << key.second << "), " << GetFitsError();
      return TCAL_FILE_ERR_ACCESS;
    }
  }
  if (status) fits_report_error(stderr, status);
  return TCAL_FILE_OK;
}


void CalibReadWriter::CalculateScaleOffset(
  const std::vector<std::vector<std::vector<std::vector<float>>>>& vector,
  uint16_t& scale, int32_t& offset) {

  GDEBUG1 << "Determining data range and defining compression resolution";

  auto nTm = vector.size();
  auto nPix = vector[0].size();
  auto dim3 = vector[0][0].size();
  auto dim4 = vector[0][0][0].size();

  float min = 9999;
  float max = -9999;
  for (uint32_t tm=0; tm<nTm; ++tm) {
    for (uint32_t pix=0; pix<nPix; ++pix) {
      for (uint32_t i3=0; i3<dim3; ++i3) {
        for (uint32_t i4=0; i4<dim4; ++i4) {
          float val = vector[tm][pix][i3][i4];
          if (val<min) min = val;
          if (val>max) max = val;
        }
      }
    }
  }
  float range = max - min;
  scale = (uint16_t)round(65535 / (range + 1));
  if (scale<1) scale = 1;
  offset = (int32_t)round(-1*min + 1) * scale;
  GDEBUG << "Compressing: min=" << min << " max="
         << max << " range=" << range
         << " scale=" << scale << " offset=" << offset;
}


int CalibReadWriter::WriteVector(
  const std::vector<std::vector<std::vector<std::vector<float>>>>& vector,
  const std::string& key,
  bool compress, uint16_t scale, int32_t offset
  ){

  GDEBUG1 << "Writing vector: " << key;

  if (!fFitsPointer) return TCAL_FILE_ERR_ACCESS;
  int status = 0;

  auto nTm = vector.size();
  auto nPix = vector[0].size();
  auto dim3 = vector[0][0].size();
  auto dim4 = vector[0][0][0].size();
  uint32_t nRows = nTm * nPix;
  uint32_t nEl = dim3 * dim4;
  uint32_t size = nRows * nEl;

  if (nRows > MAX_PIXELS){
    GERROR << "Requested number of pixels greater than "
           << " maximum allowed: " << MAX_PIXELS;
    return TCAL_FILE_ERR_NROWS;
  }

  const int tfields = 1;
  auto** ttype = new char* [tfields];
  auto** tform = new char* [tfields];
  auto** tunit = new char* [tfields];
  for(int i=0; i<tfields; i++) {
    ttype[i] = new char[20];
    tform[i] = new char[20];
    tunit[i] = new char[20];
  }
  sprintf(ttype[0],"CELLS");
  if (compress) sprintf(tform[0],"%iU",nEl);
  else sprintf(tform[0],"%iE",nEl);

  GDEBUG1 << "Creating table HDU";
  status = 0;
  if(fits_create_tbl(fFitsPointer, BINARY_TBL, 0, tfields, ttype,
                     tform, tunit, key.c_str(), &status)){
    GERROR << "Cannot create table " << GetFitsError();
    CloseFitsFile();
    return TCAL_FILE_ERR_ACCESS;
  }

  GDEBUG1 << "Preparing data for fits writing, compression = " << compress;

  if(compress) {
    auto* array_i = new uint16_t[size];
    for (uint32_t tm=0; tm<nTm; ++tm) {
      for (uint32_t pix=0; pix<nPix; ++pix) {
        for (uint32_t i3=0; i3<dim3; ++i3) {
          for (uint32_t i4=0; i4<dim4; ++i4) {
            uint32_t i = ((tm*nPix + pix) * dim3 + i3) * dim4 + i4;
            array_i[i] = (uint16_t)round(vector[tm][pix][i3][i4]*scale+offset);
          }
        }
      }
    }
    GDEBUG1 << "Writing data to fits";
    status = 0;
    fits_write_col(fFitsPointer, TUSHORT, 1, 1, 1, size, array_i, &status);
    delete[] array_i;
  }
  else {
    auto* array_f = new float[size];
    for (uint32_t tm=0; tm<nTm; ++tm) {
      for (uint32_t pix=0; pix<nPix; ++pix) {
        for (uint32_t i3=0; i3<dim3; ++i3) {
          for (uint32_t i4=0; i4<dim4; ++i4) {
            uint32_t i = ((tm*nPix + pix) * dim3 + i3) * dim4 + i4;
            array_f[i] = vector[tm][pix][i3][i4];
          }
        }
      }
    }
    GDEBUG1 << "Writing data to fits";
    status = 0;
    fits_write_col(fFitsPointer, TFLOAT, 1, 1, 1, size, array_f, &status);
    delete[] array_f;
  }
  return TCAL_FILE_OK;
}

int CalibReadWriter::WriteVector(
  const std::vector<float>& vector,
  const std::string& key
){

  GDEBUG1 << "Writing vector: " << key;

  if (!fFitsPointer) return TCAL_FILE_ERR_ACCESS;
  int status = 0;

  auto size = vector.size();

  const int tfields = 1;
  auto** ttype = new char* [tfields];
  auto** tform = new char* [tfields];
  auto** tunit = new char* [tfields];
  for(int i=0; i<tfields; i++) {
    ttype[i] = new char[20];
    tform[i] = new char[20];
    tunit[i] = new char[20];
  }
  sprintf(ttype[0],"CELLS");
  sprintf(tform[0],"%iE",1);

  GDEBUG1 << "Creating table HDU";
  status = 0;
  if(fits_create_tbl(fFitsPointer, BINARY_TBL, 0, tfields, ttype,
                     tform, tunit, key.c_str(), &status)){
    GERROR << "Cannot create table " << GetFitsError();
    CloseFitsFile();
    return TCAL_FILE_ERR_ACCESS;
  }

  GDEBUG1 << "Preparing data for fits writing";

  auto* array = new float[size];
  std::copy(vector.begin(), vector.end(), array);

  GDEBUG1 << "Writing data to fits";
  status = 0;
  fits_write_col(fFitsPointer, TFLOAT, 1, 1, 1, size, array, &status);
  if (status!=0) return TCAL_FILE_ERR_COL;
  delete[] array;

  return TCAL_FILE_OK;
}

int CalibReadWriter::WriteVector(
  const std::vector<int32_t>& vector,
  const std::string& key
){

  GDEBUG1 << "Writing vector: " << key;

  if (!fFitsPointer) return TCAL_FILE_ERR_ACCESS;
  int status = 0;

  auto size = vector.size();

  const int tfields = 1;
  auto** ttype = new char* [tfields];
  auto** tform = new char* [tfields];
  auto** tunit = new char* [tfields];
  for(int i=0; i<tfields; i++) {
    ttype[i] = new char[20];
    tform[i] = new char[20];
    tunit[i] = new char[20];
  }
  sprintf(ttype[0],"CELLS");
  sprintf(tform[0],"%iJ",1);

  GDEBUG1 << "Creating table HDU";
  status = 0;
  if(fits_create_tbl(fFitsPointer, BINARY_TBL, 0, tfields, ttype,
                     tform, tunit, key.c_str(), &status)){
    GERROR << "Cannot create table " << GetFitsError();
    CloseFitsFile();
    return TCAL_FILE_ERR_ACCESS;
  }

  GDEBUG1 << "Preparing data for fits writing";

  auto* array = new int32_t[size];
  std::copy(vector.begin(), vector.end(), array);

  GDEBUG1 << "Writing data to fits";
  status = 0;
  fits_write_col(fFitsPointer, TINT, 1, 1, 1, size, array, &status);
  if (status!=0) return TCAL_FILE_ERR_COL;
  delete[] array;

  return TCAL_FILE_OK;
}


int CalibReadWriter::WritePedestalData(
  const std::string& fileName,
  const std::vector<std::vector<std::vector<std::vector<float>>>> &ped,
  const std::vector<std::vector<std::vector<std::vector<float>>>> &hits,
  const std::vector<std::vector<std::vector<std::vector<float>>>> &std,
  bool compress
){

  GDEBUG1 << "Assigning variables from vector size";
  auto nTm = (uint32_t)ped.size();
  auto nPix = (uint32_t)ped[0].size();
  auto nBlocks = (uint32_t)ped[0][0].size();
  auto nSamplesBP = (uint32_t)ped[0][0][0].size();

  std::map<std::string, float> header;
  header["TYPE"] = FILE_TYPE_PED;
  header["TM"] = nTm;
  header["PIX"] = nPix;
  header["BLOCKS"] = nBlocks;
  header["SAMPLESBP"] = nSamplesBP;
  // TODO: Change to be generic (NDIMS, DIM0, DIM1,...)

  uint16_t scale = 0;
  int32_t offset = 0;
  if (compress) {
    CalculateScaleOffset(ped, scale, offset);
    header["SCALE"] = scale;
    header["OFFSET"] = offset;
  } 
 
  CreateFitsFile(fileName);
  WriteHeader(header);
  WriteVector(ped, "DATA", compress, scale, offset);
  if (!hits.empty()) WriteVector(hits, "HITS", false, 0, 0);
  if (!std.empty()) WriteVector(std, "STDDEV", false, 0, 0);

  return TCAL_FILE_OK;
}


int CalibReadWriter::WriteTfInput(
  const std::string& fileName, const std::vector<float>& amplitudes,
  const std::vector<std::vector<std::vector<std::vector<float>>>> &tf,
  const std::vector<std::vector<std::vector<std::vector<float>>>> &hits
){

  auto nTm = (uint32_t)tf.size();
  auto nPix = (uint32_t)tf[0].size();
  auto nCells = (uint32_t)tf[0][0].size();
  auto nPnts= (uint32_t)tf[0][0][0].size();

  std::map<std::string, float> header;
  header["TYPE"] = FILE_TYPE_TFINPUT;
  header["TM"] = nTm;
  header["PIX"] = nPix;
  header["CELLS"] = nCells;
  header["PNTS"] = nPnts;

  GDEBUG1 << "Creating fits file";
  CreateFitsFile(fileName);
  WriteHeader(header);
  WriteVector(tf, "DATA", false, 0, 0);
  WriteVector(hits, "HITS", false, 0, 0);
  WriteVector(amplitudes, "AMPLITUDES");
  CloseFitsFile();

  return TCAL_FILE_OK;
}


int CalibReadWriter::WriteTfData(
  const std::string& fileName, const std::vector<int32_t>& adcSteps,
  const std::vector<std::vector<std::vector<std::vector<float>>>> &tf,
  const bool compress
){

  auto nTm = (uint32_t)tf.size();
  auto nPix = (uint32_t)tf[0].size();
  auto nCells = (uint32_t)tf[0][0].size();
  auto nPnts = (uint32_t)tf[0][0][0].size();
  
  std::map<std::string, float> header;
  header["TYPE"] = FILE_TYPE_TF;
  header["TM"] = nTm;
  header["PIX"] = nPix;
  header["CELLS"] = nCells;
  header["PNTS"] = nPnts;

  uint16_t scale = 0;
  int32_t offset = 0;
  CalculateScaleOffset(tf, scale, offset);

  CreateFitsFile(fileName);
  WriteHeader(header);
  WriteVector(tf, "DATA", compress, scale, offset);
  WriteVector(adcSteps, "ADCSTEP");
  CloseFitsFile();
    
  return TCAL_FILE_OK;
}

int CalibReadWriter::WriteCfData(const std::string fileName,
                    const std::vector<std::vector<float>> &cf,
                                   bool compress) {
  auto nTm = (uint32_t)cf.size();
  auto nPix = (uint32_t)cf[0].size();
  
  std::map<std::string, float> header;
  header["TYPE"] = FILE_TYPE_CF;
  header["TM"] = nTm;
  header["PIX"] = nPix;

  uint16_t scale = 0;
  int32_t offset = 0;
  if (compress) {
    float min = 9999;
    float max = -9999;
    for (uint32_t tm=0; tm<nTm; ++tm) {
      for (uint32_t pix=0; pix<nPix; ++pix) {
        float val = cf[tm][pix];
        if (val<min) min = val;
        if (val>max) max = val;
      }
    }
    float range = max - min;
    scale = (uint16_t)(65535 / (range + 1));
    offset = (int32_t)(-1*min + 1) * scale;
    header["SCALE"] = scale;
    header["OFFSET"] = offset;
  } 

  GDEBUG1 << "Creating fits file";
  CreateFitsFile(fileName);
  WriteHeader(header);
  
  GDEBUG1 << "Preparing data for fits writing, compression = " << compress;
  int status = 0;
  uint32_t nrows = nTm * nPix;

  if(compress) {
    auto* cfrows_i = new uint16_t[nrows];
    for (uint32_t tm=0; tm<nTm; ++tm) {
      for (uint32_t pix=0; pix<nPix; ++pix) {
        uint32_t i = tm*nPix + pix;
        cfrows_i[i] = (uint16_t) (cf[tm][pix] * scale + offset);
      }
    }
    GDEBUG1 << "Writing data to fits";
    status = 0;
    fits_write_col(fFitsPointer, TUSHORT, 1, 1, 1, nrows, cfrows_i, &status);
    delete[] cfrows_i;
  } else {
    auto* cfrows_f = new float[nrows];
    for (uint32_t tm=0; tm<nTm; ++tm) {
      for (uint32_t pix=0; pix<nPix; ++pix) {
        uint32_t i = tm*nPix + pix;
        cfrows_f[i] = cf[tm][pix];
      }
    }
    GDEBUG1 << "Writing data to fits";
    status = 0;
    fits_write_col(fFitsPointer, TFLOAT, 1, 1, 1, nrows, cfrows_f, &status);
    delete[] cfrows_f;
  }

  if (status!=0) return TCAL_FILE_ERR_COL;

  GDEBUG1 << "Closing fits file";
  CloseFitsFile();
    
  return TCAL_FILE_OK;
}

int CalibReadWriter::ReadPedestalData(
  const std::string& fileName,
  std::vector<std::vector<std::vector<std::vector<float>>>>& ped,
  std::vector<std::vector<std::vector<std::vector<float>>>>& hits,
  std::vector<std::vector<std::vector<std::vector<float>>>>& std
){
  
    int status = 0;
    GDEBUG1 << "Opening " << fileName;
    if (fits_open_file(&fFitsPointer, fileName.c_str(), READONLY, &status)) {
      GERROR << "Cannot open " << fileName;
      return TCAL_FILE_ERR_ACCESS;
    }

    GDEBUG1 << "Reading back header";
    std::map<std::string, float> header;
    if (ReadHeader(header)!=TCAL_FILE_OK) return status;

    GDEBUG1 << "Checking file format";
    if((uint32_t)header["TYPE"]!=FILE_TYPE_PED) {
      GERROR << "This is not a pedestal file";
      return TCAL_FILE_ERR_FORMAT;
    }         
    if (CheckTable(header, HDU_CAL)!=TCAL_FILE_OK) {
      GERROR << "Table not valid";
      return TCAL_FILE_ERR_FORMAT;
    }
 
    uint32_t nTm = (uint32_t)header["TM"];
    uint32_t nPix = (uint32_t)header["PIX"];
    uint32_t nBlocks = (uint32_t)header["BLOCKS"];
    uint32_t nSamplesBP = (uint32_t)header["SAMPLESBP"];
    uint32_t nrows = nTm * nPix;
    uint32_t scale = (uint32_t) header["SCALE"];
    int32_t offset = (int32_t) header["OFFSET"];
    bool compress = (bool) header["SCALE"];
      
    GDEBUG1 << "Compression = " << compress;
    
    GDEBUG1 << "Loading data from fits table";
    if(compress) {
      auto* pedrows_i = new uint16_t[nrows*nBlocks*nSamplesBP];
      fits_read_col(fFitsPointer, TUSHORT, 1, 1, 1, nrows*nBlocks*nSamplesBP,
                    nullptr, pedrows_i, nullptr, &status);
      if (status!=0) return TCAL_FILE_ERR_COL;
      GDEBUG1 << "Parsing data to vectors";
      ped.resize(nTm);
      for (uint32_t tm=0; tm<nTm; ++tm) {
        ped[tm].resize(nPix);
        for (uint32_t pix=0; pix<nPix; ++pix) {
          ped[tm][pix].resize(nBlocks);
          for (uint32_t blk=0; blk<nBlocks; ++blk) {
            ped[tm][pix][blk].resize(nSamplesBP);
            for (uint32_t sampbp=0; sampbp<nSamplesBP; ++sampbp) {
              uint32_t i = ((tm*nPix + pix)*nBlocks + blk) * nSamplesBP +sampbp;
              ped[tm][pix][blk][sampbp] = ((float)pedrows_i[i] - offset) /scale;
            }
          }
        }
      }
      delete[] pedrows_i;
    } else {
      auto* pedrows_f = new float[nrows*nBlocks*nSamplesBP];
      fits_read_col(fFitsPointer, TFLOAT, 1, 1, 1, nrows*nBlocks*nSamplesBP,
                    nullptr, pedrows_f, nullptr, &status);
      if (status!=0) return TCAL_FILE_ERR_COL;
      GDEBUG1 << "Parsing data to vectors";
      ped.resize(nTm);
      for (uint32_t tm=0; tm<nTm; ++tm) {
        ped[tm].resize(nPix);
        for (uint32_t pix=0; pix<nPix; ++pix) {
          ped[tm][pix].resize(nBlocks);
          for (uint32_t blk=0; blk<nBlocks; ++blk) {
            ped[tm][pix][blk].resize(nSamplesBP);
            for (uint32_t sampbp=0; sampbp<nSamplesBP; ++sampbp) {
              uint32_t i = ((tm*nPix + pix)*nBlocks + blk) * nSamplesBP +sampbp;
              ped[tm][pix][blk][sampbp] = pedrows_f[i];
            }
          }
        }
      }
      delete[] pedrows_f;
    }

    if (!fits_movnam_hdu(fFitsPointer, BINARY_TBL, (char*)"HITS", 0, &status)) {
      auto* hitrows = new float[nrows*nBlocks*nSamplesBP];
      fits_read_col(fFitsPointer, TFLOAT, 1, 1, 1, nrows*nBlocks*nSamplesBP,
                    nullptr, hitrows, nullptr, &status);
      if (status!=0) return TCAL_FILE_ERR_COL;
      GDEBUG1 << "Parsing data to vectors";
      hits.resize(nTm);
      for (uint32_t tm=0; tm<nTm; ++tm) {
        hits[tm].resize(nPix);
        for (uint32_t pix=0; pix<nPix; ++pix) {
          hits[tm][pix].resize(nBlocks);
          for (uint32_t blk=0; blk<nBlocks; ++blk) {
            hits[tm][pix][blk].resize(nSamplesBP);
            for (uint32_t sampbp=0; sampbp<nSamplesBP; ++sampbp) {
              uint32_t i = ((tm*nPix + pix)*nBlocks + blk) * nSamplesBP +sampbp;
              hits[tm][pix][blk][sampbp] = hitrows[i];
            }
          }
        }
      }
      delete[] hitrows;
    }

  if (!fits_movnam_hdu(fFitsPointer, BINARY_TBL, (char*)"STDDEV", 0, &status)) {
    auto* stdrows = new float[nrows*nBlocks*nSamplesBP];
    fits_read_col(fFitsPointer, TFLOAT, 1, 1, 1, nrows*nBlocks*nSamplesBP,
                  nullptr, stdrows, nullptr, &status);
    if (status!=0) return TCAL_FILE_ERR_COL;
    GDEBUG1 << "Parsing data to vectors";
    std.resize(nTm);
    for (uint32_t tm=0; tm<nTm; ++tm) {
      std[tm].resize(nPix);
      for (uint32_t pix=0; pix<nPix; ++pix) {
        std[tm][pix].resize(nBlocks);
        for (uint32_t blk=0; blk<nBlocks; ++blk) {
          std[tm][pix][blk].resize(nSamplesBP);
          for (uint32_t sampbp=0; sampbp<nSamplesBP; ++sampbp) {
            uint32_t i = ((tm*nPix + pix)*nBlocks + blk) * nSamplesBP +sampbp;
            std[tm][pix][blk][sampbp] = stdrows[i];
          }
        }
      }
    }
    delete[] stdrows;
  }
    
    GDEBUG1 << "Closing fits file";
    CloseFitsFile();

    return TCAL_FILE_OK;
}

  
int CalibReadWriter::ReadTfInput(
  const std::string& fileName,
  std::vector<float>& amplitude,
  std::vector<std::vector<std::vector<std::vector<float>>>>& tf,
  std::vector<std::vector<std::vector<std::vector<float>>>>& hits
){

  int status = 0;
  GDEBUG1 << "Opening " << fileName;
  if (fits_open_file(&fFitsPointer, fileName.c_str(), READONLY, &status)) {
    GERROR << "Cannot open " << fileName;
    return TCAL_FILE_ERR_ACCESS;
  }

  GDEBUG1 << "Reading back header";
  std::map<std::string, float> header;
  if (ReadHeader(header)!=TCAL_FILE_OK) return status;

  GDEBUG1 << "Checking file format";
  if((uint32_t)header["TYPE"]!=FILE_TYPE_TFINPUT) {
    GERROR << "This is not a tf file";
    return TCAL_FILE_ERR_FORMAT;
  }
  if (CheckTable(header, HDU_CAL)!=TCAL_FILE_OK) {
    GERROR << "Table not valid";
    return TCAL_FILE_ERR_FORMAT;
  }

  uint32_t nTm = (uint32_t)header["TM"];
  uint32_t nPix = (uint32_t)header["PIX"];
  uint32_t nCells = (uint32_t)header["CELLS"];
  uint32_t nPnts= (uint32_t)header["PNTS"];
  uint32_t nrows = nTm*nPix;

  GDEBUG1 << "Loading data from fits table";
  auto* tfrows_f = new float[nrows*nCells*nPnts];
  fits_read_col(fFitsPointer, TFLOAT, 1, 1, 1, nrows*nCells*nPnts,
                nullptr, tfrows_f, nullptr, &status);
  if (status!=0) return TCAL_FILE_ERR_COL;

  char* key = (char*)"HITS";
  if (fits_movnam_hdu(fFitsPointer, BINARY_TBL, key, 0, &status)) {
    GERROR << "Cannot move to the HDU (" << key << ") " <<  GetFitsError();
    return TCAL_FILE_ERR_FORMAT;
  }
  auto* hitsrows_f = new float[nrows*nCells*nPnts];
  fits_read_col(fFitsPointer, TFLOAT, 1, 1, 1, nrows*nCells*nPnts,
                nullptr, hitsrows_f, nullptr, &status);
  if (status!=0) return TCAL_FILE_ERR_COL;

  key = (char*)"AMPLITUDES";
  if (fits_movnam_hdu(fFitsPointer, BINARY_TBL, key, 0, &status)) {
    GERROR << "Cannot move to the HDU (" << key << ") " <<  GetFitsError();
    return TCAL_FILE_ERR_FORMAT;
  }
  auto* amprows = new float[nPnts];
  fits_read_col(fFitsPointer, TFLOAT, 1, 1, 1, nPnts,
                nullptr, amprows, nullptr, &status);
  if (status!=0) return TCAL_FILE_ERR_COL;

  GDEBUG1 << "Parsing data to vectors";
  tf.resize(nTm);
  hits.resize(nTm);
  for (uint32_t tm=0; tm<nTm; ++tm) {
    tf[tm].resize(nPix);
    hits[tm].resize(nPix);
    for (uint32_t pix=0; pix<nPix; ++pix) {
      tf[tm][pix].resize(nCells);
      hits[tm][pix].resize(nCells);
      for (uint32_t cell=0; cell<nCells; ++cell) {
        tf[tm][pix][cell].resize(nPnts);
        hits[tm][pix][cell].resize(nPnts);
        for (uint32_t pnt=0; pnt<nPnts; ++pnt) {
          uint32_t i = ((tm * nPix + pix) * nCells + cell) * nPnts + pnt;
          tf[tm][pix][cell][pnt] = tfrows_f[i];
          hits[tm][pix][cell][pnt] = hitsrows_f[i];
        }
      }
    }
  }

  amplitude.resize(nPnts);
  for (uint32_t pnt=0; pnt<nPnts; ++pnt) {
    amplitude[pnt] = amprows[pnt];
  }

  GDEBUG1 << "Closing fits file";
  CloseFitsFile();

  delete[] tfrows_f;
  delete[] hitsrows_f;
  delete[] amprows;

  return TCAL_FILE_OK;
}

int CalibReadWriter::ReadTfData(
  const std::string& fileName,
  std::vector<int32_t>& adcSteps,
  std::vector<std::vector<std::vector<std::vector<float>>>>& tf
){

  int status = 0;
  GDEBUG1 << "Opening " << fileName;
  if (fits_open_file(&fFitsPointer, fileName.c_str(), READONLY, &status)) {
    GERROR << "Cannot open " << fileName;
    return TCAL_FILE_ERR_ACCESS;
  }

  GDEBUG1 << "Reading back header";
  std::map<std::string, float> header;
  if (ReadHeader(header)!=TCAL_FILE_OK) return status;
  
  GDEBUG1 << "Checking file format";
  if((uint32_t)header["TYPE"]!=FILE_TYPE_TF) {
    GERROR << "This is not a tf file";
    return TCAL_FILE_ERR_FORMAT;
  }         
  if (CheckTable(header, HDU_CAL)!=TCAL_FILE_OK) {
    GERROR << "Table not valid";
    return TCAL_FILE_ERR_FORMAT;
  }
  
  uint32_t nTm = (uint32_t)header["TM"];
  uint32_t nPix = (uint32_t)header["PIX"];
  uint32_t nCells = (uint32_t)header["CELLS"];
  uint32_t nPnts= (uint32_t)header["PNTS"];
  uint32_t nrows = nTm*nPix;
  float scale = header["SCALE"];
  int32_t offset = (int32_t)header["OFFSET"];
  bool compress = (bool)header["SCALE"];
  
  GDEBUG1 << "Compression = " << compress;

  GDEBUG1 << "Loading data from fits table";
  if(compress) {
    auto* tfrows_i = new uint16_t[nrows*nCells*nPnts];
    fits_read_col(fFitsPointer, TUSHORT, 1, 1, 1, nrows*nCells*nPnts,
                  nullptr, tfrows_i, nullptr, &status);
    if (status!=0) return TCAL_FILE_ERR_COL;
    GDEBUG1 << "Parsing data to vectors";
    tf.resize(nTm);
    for (uint32_t tm=0; tm<nTm; ++tm) {
      tf[tm].resize(nPix);
      for (uint32_t pix=0; pix<nPix; ++pix) {
        tf[tm][pix].resize(nCells);
        for (uint32_t cell=0; cell<nCells; ++cell) {
          tf[tm][pix][cell].resize(nPnts);
          for (uint32_t pnt=0; pnt<nPnts; ++pnt) {
            uint32_t i = ((tm * nPix + pix) * nCells + cell) * nPnts + pnt;
            tf[tm][pix][cell][pnt] = ((float)tfrows_i[i] - offset) / scale;
          }
        }
      }
    }
    delete[] tfrows_i;
  }
  else {
    auto* tfrows_f = new float[nrows*nCells*nPnts];
    fits_read_col(fFitsPointer, TFLOAT, 1, 1, 1, nrows*nCells*nPnts,
                  nullptr, tfrows_f, nullptr, &status);
    if (status!=0) return TCAL_FILE_ERR_COL;
    GDEBUG1 << "Parsing data to vectors";
    tf.resize(nTm);
    for (uint32_t tm=0; tm<nTm; ++tm) {
      tf[tm].resize(nPix);
      for (uint32_t pix=0; pix<nPix; ++pix) {
        tf[tm][pix].resize(nCells);
        for (uint32_t cell=0; cell<nCells; ++cell) {
          tf[tm][pix][cell].resize(nPnts);
          for (uint32_t pnt=0; pnt<nPnts; ++pnt) {
            uint32_t i = ((tm * nPix + pix) * nCells + cell) * nPnts + pnt;
            tf[tm][pix][cell][pnt] = tfrows_f[i];
          }
        }
      }
    }
    delete[] tfrows_f;
  }

  char* key = (char*)"ADCSTEP";
  if (fits_movnam_hdu(fFitsPointer, BINARY_TBL, key, 0, &status)) {
    GERROR << "Cannot move to the HDU (" << key << ") " <<  GetFitsError();
    return TCAL_FILE_ERR_FORMAT;
  }
  auto* adcsteprows = new int32_t[nPnts];
  fits_read_col(fFitsPointer, TINT, 1, 1, 1, nPnts,
                nullptr, adcsteprows, nullptr, &status);
  if (status!=0) return TCAL_FILE_ERR_COL;

  adcSteps.resize(nPnts);
  for (uint32_t pnt=0; pnt<nPnts; ++pnt) {
    adcSteps[pnt] = adcsteprows[pnt];
  }
  delete[] adcsteprows;

  GDEBUG1 << "Closing fits file";
  CloseFitsFile();

  return TCAL_FILE_OK;
}

int CalibReadWriter::ReadCfData(const std::string fileName,
                                  std::vector<std::vector<float>>& cf){
  
    int status = 0;
    GDEBUG1 << "Opening " << fileName;
    if (fits_open_file(&fFitsPointer, fileName.c_str(), READONLY, &status)) {
      GERROR << "Cannot open " << fileName;
      return TCAL_FILE_ERR_ACCESS;
    }

    GDEBUG1 << "Reading back header";
    std::map<std::string, float> header;
    if (ReadHeader(header)!=TCAL_FILE_OK) return status;

    GDEBUG1 << "Checking file format";
    if((uint32_t)header["TYPE"]!=FILE_TYPE_CF) {
      GERROR << "This is not a gain file";
      return TCAL_FILE_ERR_FORMAT;
    }         
    if (CheckTable(header, HDU_CAL)!=TCAL_FILE_OK) {
      GERROR << "Table not valid";
      return TCAL_FILE_ERR_FORMAT;
    }
 
    uint32_t nTm = (uint32_t)header["TM"];
    uint32_t nPix = (uint32_t)header["PIX"];
    uint32_t nrows = nTm*nPix;
    float scale = header["SCALE"];
    int32_t offset = (int32_t)header["OFFSET"];
    bool compress = (bool)header["SCALE"];
      
    GDEBUG1 << "Compression = " << compress;

    GDEBUG1 << "Loading data from fits table";
    if(compress) {
      auto* cfrows_i = new uint16_t[nrows];
      fits_read_col(fFitsPointer, TUSHORT, 1, 1, 1, nrows,
                    nullptr, cfrows_i, nullptr, &status);
      if (status!=0) return TCAL_FILE_ERR_COL;
      GDEBUG1 << "Parsing data to vectors";
      cf.resize(nTm);
      for (uint32_t tm=0; tm<nTm; ++tm) {
        cf[tm].resize(nPix);
        for (uint32_t pix=0; pix<nPix; ++pix) {
          uint32_t i = tm*nPix + pix;
          cf[tm][pix] = ((float)cfrows_i[i] - offset) / scale;
        }
      }
      delete[] cfrows_i;
    }
    else {
      auto* cfrows_f = new float[nrows];
      fits_read_col(fFitsPointer, TFLOAT, 1, 1, 1, nrows,
                    nullptr, cfrows_f, nullptr, &status);
      if (status!=0) return TCAL_FILE_ERR_COL;
      GDEBUG1 << "Parsing data to vectors";
      cf.resize(nTm);
      for (uint32_t tm=0; tm<nTm; ++tm) {
        cf[tm].resize(nPix);
        for (uint32_t pix=0; pix<nPix; ++pix) {
          uint32_t i = tm*nPix + pix;
          cf[tm][pix] = cfrows_f[i];
        }
      }
      delete[] cfrows_f;
    }
    
    GDEBUG1 << "Closing fits file";
    CloseFitsFile();

    return TCAL_FILE_OK;
}
  
int CalibReadWriter::CloseFitsFile() {

  GDEBUG1 << "Closing FITS file";

  if (!fFitsPointer) return TCAL_FILE_OK;
  
  int status = 0;
  if (fits_close_file(fFitsPointer, &status)) {
    GERROR << "Cannot close the file " << GetFitsError();
    return TCAL_FILE_ERR_ACCESS;
  } else {
    fFitsPointer = nullptr;
  }
  return TCAL_FILE_OK;
}

std::string CalibReadWriter::GetFitsError(){
	if (!fFitsPointer) return nullptr;
	int status = 0;
	char errorRaw[200];
	fits_get_errstatus(status, errorRaw);
	std::string errorMsg = "FITS ERR:";
	return errorMsg.append(errorRaw);
}

int CalibReadWriter::ReadHeader(std::map<std::string, float>& header, int hdu){
  if (!fFitsPointer) return TCAL_FILE_ERR_ACCESS;

  int status = 0;
  int hdutype;
  GDEBUG1 << "Moving to header HDU";
  if (fits_movabs_hdu(fFitsPointer, hdu, &hdutype, &status)) {
    GERROR << "Cannot move to the header HDU, "<<  GetFitsError();
    return TCAL_FILE_ERR_FORMAT;
  }
  
  status = 0;
  char key[FLEN_VALUE], value[FLEN_VALUE], comment[FLEN_COMMENT];
  bool done = false;
  int keyNum = 1;
  GDEBUG1 << "Reading header key, value pairs";
  while(!done) {
    if (fits_read_keyn(fFitsPointer, keyNum, key, value, comment,
                       &status)) {
      GERROR << "Error reading key, value pairs";
      return TCAL_FILE_ERR_KEYWORD_TYPE;
    }
    if (std::strcmp(key,"END")==0) {
      done = true;
    }
    else {
      GDEBUG1 << keyNum << ", Key=" << key << " Val=" << value;
      header[std::string(key)] = (float)std::atof(value); // NOLINT
      keyNum++;
    }
  }
  
  if (status) fits_report_error(stderr, status);
  return TCAL_FILE_OK;
}

int CalibReadWriter::CheckTable(std::map<std::string, float> header, int hdu) {

  std::map<std::string, float> headerTable;
  GDEBUG1 << "Reading back table header";
  ReadHeader(headerTable, hdu); 
  uint32_t nAx = (uint32_t)headerTable["NAXIS"];
  if (nAx!=2) {
   GERROR << "Incorrect number of axis in fits table:" << nAx << ", required 2";
   return TCAL_FILE_ERR_FORMAT;
  }

  int status = 0;
  int nhdu = -99;
  GDEBUG1 << "Checking number of HDU";
  if (fits_get_num_hdus(fFitsPointer, &nhdu, &status)) {
    GERROR << "Cannot read number of HDUs, " << GetFitsError();
    return TCAL_FILE_ERR_FORMAT;
  }

  if(nhdu<2 || nhdu>4) {
    GERROR << "Incorrect number of HDU found (should be between 2 or 4): "
           << nhdu;
    return TCAL_FILE_ERR_FORMAT;
  }

   status = 0;
   int hdutype = -99;
    GDEBUG1 << "Checking HDU types";
   if (fits_movabs_hdu(fFitsPointer, hdu, &hdutype, &status)) {
     GERROR << "Cannot move to requested hdu " <<  GetFitsError();
     return TCAL_FILE_ERR_FORMAT;
  }
  if(hdutype!=BINARY_TBL) {
    GERROR << "Incorrect HDU type (should be " << BINARY_TBL << "): "
           << hdutype;
    return TCAL_FILE_ERR_FORMAT;
  }

  status = 0;
  long nrowsl;
  GDEBUG1 << "Checking number of rows in table";
  if (fits_get_num_rows(fFitsPointer, &nrowsl, &status)) {
    GERROR << "Cannot read the number of rows, " <<  GetFitsError();
    return TCAL_FILE_ERR_FORMAT;
  }
 
  if (nrowsl > MAX_PIXELS) return TCAL_FILE_ERR_NROWS;
  auto nrows = (int) nrowsl;

  if (hdu==HDU_CAL) {
    int nrowsExpected = (int)(header["TM"] * header["PIX"]);
    if (nrows != nrowsExpected) {
      GERROR << "Expected " << nrowsExpected << " got " << nrows;
      return TCAL_FILE_ERR_FORMAT;
    }
  }

  status = 0;
  int ncols;
  GDEBUG1 << "Checking number of columns in table";
  if (fits_get_num_cols(fFitsPointer, &ncols, &status)) {
    GERROR << "Cannot read the number of cols, " <<  GetFitsError();
    return TCAL_FILE_ERR_FORMAT;
  }

  if (hdu == HDU_CAL && ncols != 1) {
    GERROR << "Expected 3 columns, got " << ncols;
    return TCAL_FILE_ERR_FORMAT;
  }

  return TCAL_FILE_OK;
}

}  // namespace TargetCalib
}  // namespace CTA
