%module target_io
#pragma SWIG nowarn=362,389,503

%feature("autodoc", "1");

%include "typemaps.i"
%include "std_shared_ptr.i"
%shared_ptr(CTA::TargetDriver::TDataPacket);
%shared_ptr(CTA::TargetDriver::RawEvent);
%shared_ptr(CTA::TargetDriver::EventBuffer)
%shared_ptr(CTA::TargetIO::FitsCardImage)
%shared_ptr(CTA::TargetIO::EventFileWriter)

%{
#define SWIG_FILE_WITH_INIT
#include <TargetDriver/Waveform.h>
#include <TargetDriver/DataPacket.h>
#include <TargetDriver/EventHeader.h>
#include <TargetDriver/RawEvent.h>
#include <TargetDriver/EventBuffer.h>
#include <TargetDriver/DataListener.h>
#include "TargetIO/EventFileWriter.h"
#include "TargetIO/FitsKeyValue.h"
#include "TargetIO/FitsCardImage.h"
#include "TargetIO/EventFile.h"
#include "TargetIO/EventFileReader.h"
#include "TargetIO/WaveformArrayReader.h"
%}

%include "std_list.i"
%include "std_vector.i"
%include "std_set.i"
%include "std_string.i"
%include "stdint.i"
%include "typemaps.i"

%include "numpy.i"
%init %{
    import_array();
%}

%numpy_typemaps(uint64_t, NPY_ULONGLONG, int)

%apply uint16_t *OUTPUT { uint16_t& first_cell_id };
%apply bool *OUTPUT { bool& stale, bool& missing_packets };
%apply uint64_t *OUTPUT { uint64_t& tack };
%apply int64_t *OUTPUT { int64_t& cpu_s, int64_t& cpu_ns };

%apply (unsigned short* ARGOUT_ARRAY1, int DIM1) {(uint16_t* adcarray, uint16_t n)}
%apply (unsigned short* INPLACE_ARRAY2, int DIM1, int DIM2) {(uint16_t* waveforms, size_t n_pixels_w, size_t n_samples_w)}
%apply (float* INPLACE_ARRAY2, int DIM1, int DIM2) {(float* waveforms, size_t n_pixels_w, size_t n_samples_w)}

%include <TargetDriver/Waveform.h>
%include <TargetDriver/DataPacket.h>
%include <TargetDriver/EventHeader.h>
%include <TargetDriver/RawEvent.h>
%include <TargetDriver/EventBuffer.h>
%include <TargetDriver/DataListener.h>
%include "TargetIO/EventFileWriter.h"
%include "TargetIO/FitsKeyValue.h"
%include "TargetIO/FitsCardImage.h"
%include "TargetIO/EventFile.h"
%include "TargetIO/EventFileReader.h"
%include "TargetIO/WaveformArrayReader.h"

%template(VectorDataPacketSharedPtr) std::vector<std::shared_ptr<CTA::TargetDriver::DataPacket> >;
