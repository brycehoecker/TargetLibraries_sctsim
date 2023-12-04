%module target_calib
#pragma SWIG nowarn=362,389,503

%feature("autodoc", "1");

%{
#define SWIG_FILE_WITH_INIT
#include "TargetCalib/Constants.h"
#include "TargetCalib/Calibrator.h"
#include "TargetCalib/CalibratorMultiFile.h"
#include "TargetCalib/CalibReadWriter.h"
#include "TargetCalib/CalibArrayReader.h"
#include "TargetCalib/CfMaker.h"
#include "TargetCalib/Logger.h"
#include "TargetCalib/PedestalMaker.h"
#include "TargetCalib/TfMaker.h"
#include "TargetCalib/Utils.h"
#include "TargetCalib/MappingSP.h"
#include "TargetCalib/MappingTM.h"
#include "TargetCalib/Mapping.h"
#include "TargetCalib/RunningStats.h"
#include "TargetCalib/CameraConfiguration.h"

using namespace CTA::TargetCalib;
%}

%include "std_vector.i"
%include "std_vector.i"
%include "std_set.i"
%include "std_list.i"
%include "std_string.i"
%include "stdint.i"
%include "typemaps.i"

%template(FloatVector) std::vector<float>;
%template(DoubleVector) std::vector<double>;
%template(UInt16Vector) std::vector<uint16_t>;
%template(Int16Vector) std::vector<int16_t>;
%template(IntVector) std::vector<int>;
%template(FloatVector2D) std::vector<std::vector<float>>;
%template(FloatVector3D) std::vector<std::vector<std::vector<float>>>;
%template(FloatVector4D) std::vector<std::vector<std::vector<std::vector<float>>>>;
%template(StringVector) std::vector<std::string>;
%template(UInt16Set) std::set<uint16_t>;

%apply int *OUTPUT { uint16_t& pRow, uint16_t& pColumn, uint16_t& pBlockPhase };

%include "numpy.i"
%init %{
    import_array();
%}

// Calibrator::ApplyEvent, PedestalMaker::AddEvent
%apply (unsigned short* IN_ARRAY1, int DIM1) {(const uint16_t* wf, const size_t nSamples)}
%apply (unsigned short* IN_ARRAY2, int DIM1, int DIM2) {(const uint16_t* wfs, size_t nPix, size_t nSamples)}
%apply (unsigned short* IN_ARRAY1, int DIM1) {(const uint16_t* fci, size_t fciNPix)}
%apply (float* INPLACE_ARRAY2, int DIM1, int DIM2) {(float* wfsC, size_t nPixC, size_t nSamplesC)}
%apply (float* IN_ARRAY1, int DIM1) {(const float* wf, const size_t nSamples_i)}
%apply (float* INPLACE_ARRAY1, int DIM1) {(float* wfCal, const size_t nSamples_o)}

// TfMaker::TfMaker
%apply (short* IN_ARRAY1, int DIM1) {(const int16_t* vpedArr, const size_t nVpedPnt)}

// TfMaker::AddEvent
%apply (float* IN_ARRAY2, int DIM1, int DIM2) {(const float* wfs, const size_t nPix, const size_t nSamples)}

// CfMaker
%apply (float* IN_ARRAY1, int DIM1) {(const float* cf, const size_t cfSize)}

// Utils
%apply (unsigned short* IN_ARRAY1, int DIM1, unsigned short* ARGOUT_ARRAY1, unsigned short* ARGOUT_ARRAY1, unsigned short* ARGOUT_ARRAY1) {(const uint16_t* pCellId, const size_t sizeCellID, uint16_t* pRow, uint16_t* pColumn, uint16_t* pBlockPhase)}
%apply (unsigned short* IN_ARRAY1, int DIM1) {(const uint16_t* firstCellID, const size_t sizeFirstCellID)}
%apply (unsigned short* IN_ARRAY1, int DIM1, unsigned short* ARGOUT_ARRAY1) {(const uint16_t* sample, const size_t sizeSample, uint16_t* cellID)}

// RunningStats
%apply (double* IN_ARRAY1, int DIM1) {(double* array, size_t array_size)}

// OLD
//%apply (unsigned short* IN_ARRAY1, int DIM1) {(const uint16_t* tm, const size_t tmSize)}
//%apply (unsigned short* IN_ARRAY1, int DIM1) {(const uint16_t* tmpix, const size_t tmpixSize)}
//%apply (unsigned short* IN_ARRAY1, int DIM1) {(const uint16_t* vped, const size_t nVpedPnt)}
//%apply (unsigned short* IN_ARRAY1, int DIM1) {(const uint16_t* startCells, const size_t startCellsSize)}

//%apply (unsigned short* IN_ARRAY1, int DIM1) {(const uint16_t* wf, const size_t nSamples)}
//%apply (unsigned short* INPLACE_ARRAY1, int DIM1) {(uint16_t* wfCal, const size_t nCalSamples)}
//%apply (float* INPLACE_ARRAY1, int DIM1) {(float* wfCal, const size_t nCalSamples)}
//%apply (float* INPLACE_ARRAY1, int DIM1) {(float* wfFloat, const size_t nFloatSamples)}

//%apply (unsigned short* IN_ARRAY1, int DIM1) {(const uint16_t* startCells, const size_t nPixels_c)}
//%apply (unsigned short* IN_ARRAY2, int DIM1, int DIM2) {(const uint16_t* pix2tmtmpix, const size_t nPixels, const size_t nDim)}
//%apply (unsigned short* IN_ARRAY2, int DIM1, int DIM2) {(const uint16_t* wfs, const size_t nPixels_wr, const size_t nSamples_wr)}
//%apply (float* INPLACE_ARRAY2, int DIM1, int DIM2) {(float* wfsCal, const size_t nPixels_wc, const size_t nSamples_wc)}
//%apply (unsigned short* INPLACE_ARRAY2, int DIM1, int DIM2) {(uint16_t* wfsCal, const size_t nPixels_wc, const size_t nSamples_wc)}

%extend CTA::TargetCalib::Version {
    std::string __str__() const {
         std::ostringstream out;
         out << *$self;
         return out.str();
    }
}

%extend CTA::TargetCalib::Mapping {
	%pythoncode %{
		def as_dataframe(self):
			import numpy as np
			import pandas as pd
			df = pd.DataFrame(dict(
				pixel=np.array(self.GetPixelVector(), dtype=np.uint16),
				slot=np.array(self.GetSlotVector(), dtype=np.uint16),
				asic=np.array(self.GetASICVector(), dtype=np.uint16),
				channel=np.array(self.GetChannelVector(), dtype=np.uint16),
				tmpix=np.array(self.GetTMPixelVector(), dtype=np.uint16),
				row=np.array(self.GetRowVector(), dtype=np.uint16),
				col=np.array(self.GetColumnVector(), dtype=np.uint16),
				sipmpix=np.array(self.GetSipmPixVector(), dtype=np.uint16),
				superpixel=np.array(self.GetSuperPixelVector(), dtype=np.uint16),
				xpix=np.array(self.GetXPixVector(), dtype=np.double),
				ypix=np.array(self.GetYPixVector(), dtype=np.double)
			))
			return df
	%}
};

%include "TargetCalib/Constants.h"
%include "TargetCalib/Calibrator.h"
%include "TargetCalib/CalibratorMultiFile.h"
%include "TargetCalib/CalibReadWriter.h"
%include "TargetCalib/CalibArrayReader.h"
%include "TargetCalib/CfMaker.h"
%include "TargetCalib/Logger.h"
%include "TargetCalib/PedestalMaker.h"
%include "TargetCalib/TfMaker.h"
%include "TargetCalib/Utils.h"
%include "TargetCalib/MappingSP.h"
%include "TargetCalib/MappingTM.h"
%include "TargetCalib/Mapping.h"
%include "TargetCalib/RunningStats.h"
%include "TargetCalib/CameraConfiguration.h"
