// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include <cmath>
#include <algorithm>  // Included for bryces code for std::min
#include <cstring>    // Include for bryces code std::memcpy

#include "TargetDriver/Waveform.h"

namespace CTA {
	namespace TargetDriver {		
		//Basically copy all data into an array in a very inefficient way
		void Waveform::GetADCArray(uint16_t* adcarray = NULL, uint16_t n = 0) const {
			if (adcarray == NULL) {
				std::cerr << "WARNING: need to allocate memory before calling this method" << std::endl;
			}
			uint16_t nmax = GetSamples();
			if (nmax != n) {
				std::cerr << "WARNING: number of samples in method argument should be equal to Waveform::GetSamples()" << std::endl;
			}
			for (uint16_t i = 0; i < n and i < nmax; i++) { adcarray[i] = GetADC(i); }  // i
		}//void Waveform::GetADCArray
		//Basically copy all data into an array in a very inefficient way
		void Waveform::GetADC16bitArray(uint16_t* adcarray = NULL, uint16_t n = 0) const {
			if (adcarray == NULL) {
				std::cerr << "WARNING: need to allocate memory before calling this method" << std::endl;
			}
			uint16_t nmax = GetSamples();
			if (nmax != n) {
				std::cerr << "WARNING: number of samples in method argument should be equal to Waveform::GetSamples()" << std::endl;
			}
			for (uint16_t i = 0; i < n and i < nmax; i++) { adcarray[i] = GetADC16bit(i); }  // i
		}//void Waveform::GetADC16bitArray

		
		// Bryce Hoecker is trying to rewrite the above functions to no longer be "very inefficient"

		// Function to get ADC array from the waveform.
		void Waveform::brycesGetADCArray(uint16_t* adcarray, uint16_t n) const {
			// Check if the adcarray pointer is NULL. If it is, print an error and return.
			if (adcarray == NULL) {
				std::cerr << "ERROR: adcarray is NULL." << std::endl;
				return;
			}

			// Retrieve the number of samples in the waveform.
			uint16_t nmax = GetSamples();
			// Check if the provided number of samples (n) matches the actual number of samples (nmax).
			// If not, print an error and return.
			if (nmax != n) {
				std::cerr << "ERROR: Number of samples does not match." << std::endl;
				return;
			}

			// If direct memory copying is possible, use std::memcpy to copy the data.
			// Replace 'sourceArray' with the actual source array of waveform data.
			// std::memcpy(adcarray, sourceArray, nmax * sizeof(uint16_t));

			// If direct bulk copy is not possible, use a loop to copy each sample individually.
			// Loop over each sample and copy it to the adcarray.
			for (uint16_t i = 0; i < n; ++i) { 
				adcarray[i] = GetADC(i); // Get the i-th ADC value and store it in the adcarray.
			}
		}//void Waveform::brycesGetADCArray

		// Function to get 16-bit ADC array from the waveform.
		void Waveform::brycesGetADC16bitArray(uint16_t* adcarray, uint16_t n) const {
			// Check if the adcarray pointer is NULL. If it is, print an error and return.
			if (adcarray == NULL) {
				std::cerr << "ERROR: adcarray is NULL." << std::endl;
				return;
			}

			// Retrieve the number of samples in the waveform.
			uint16_t nmax = GetSamples();
			// Check if the provided number of samples (n) matches the actual number of samples (nmax).
			// If not, print an error and return.
			if (nmax != n) {
				std::cerr << "ERROR: Number of samples does not match." << std::endl;
				return;
			}

			// If direct memory copying is possible, use std::memcpy to copy the data.
			// Replace 'sourceArray' with the actual source array of waveform data.
			// std::memcpy(adcarray, sourceArray, nmax * sizeof(uint16_t));

			// If direct bulk copy is not possible, use a loop to copy each sample individually.
			// Loop over each sample and copy it to the adcarray.
			for (uint16_t i = 0; i < n; ++i) {
				adcarray[i] = GetADC16bit(i); // Get the i-th 16-bit ADC value and store it in the adcarray.
			}
		}//void Waveform::brycesGetADC16bitArray


		// Calculates mean and std. dev. of first maxsamples ADC values.
		// See
		// https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Online_algorithm
		// for the algorithm used here.
		// In case of error, stddev is set to -1.
		// Note that Waveform::GetMeanAndRMS should not be used because the
		// implementation in this file has two bugs.
		// Also note that RMS and standard deviation are different.
		void Waveform::GetMeanAndStdDev(float& mean, float& stddev, uint16_t maxsamples) {
			uint16_t nmax = GetSamples();
			if (maxsamples > 1 && maxsamples < nmax) { nmax = maxsamples; }
			mean = 0.0;
			if (nmax < 1) {
				stddev = -1;
				return;
			}
			float M2 = 0.0;
			for (uint16_t i = 0; i < nmax; ++i) {
				float newValue = GetADC(i);
				float delta = newValue - mean;
				mean += delta / (i + 1);
				float delta2 = newValue - mean;
				M2 += delta * delta2;
			}
			if (M2 < 0) { stddev = -1; }
			else { stddev = std::sqrt(M2 / nmax); }
			return;
		}//void Waveform::GetMeanAndStdDev

		void Waveform::GetMeanAndRMS(float& mean, float& rms, uint16_t maxsamples) {
			std::cerr << "WARNING: Waveform::GetMeanAndRMS is obsolete and buggy. Use Waveform::GetMeanAndStdDev instead." << std::endl;
			uint16_t nmax = GetSamples();
			if (maxsamples > 1 && maxsamples < nmax) { nmax = maxsamples; }
			mean = 0.0;
			if (nmax < 1) {
				rms = -1;
				return;
			}
			float M2 = 0.0;
			for (uint16_t i = 1; i < nmax; ++i) {
				float newValue = GetADC(i);
				float delta = newValue - mean;
				mean += delta / i;
				float delta2 = newValue - mean;
				M2 += delta * delta2;
			}
			if (M2 < 0) { rms = -1; }
			else { rms = std::sqrt(M2 / (float)(nmax)); }
			return;
		}//void Waveform::GetMeanAndRMS

		// The remaining methods are used for simulations...
		void Waveform::SetADC(uint16_t n, uint16_t val) {  // For use in simulation mode
			// TODO(Harm) - checking bounds    if (3 + 2 * n > ...)
			fData[2 + 2 * n] = (val >> 8) & 0xF;
			fData[3 + 2 * n] = (val & 0xFF);
		}//void Waveform::SetADC

		void Waveform::SetADC16bit(uint16_t n, uint16_t val) {  // For use in simulation mode
			// TODO(Harm) - checking bounds    if (3 + 2 * n > ...)
			fData[2 + 2 * n] = (val >> 8);
			fData[3 + 2 * n] = (val & 0xFF);
		}//void Waveform::SetADC16bit

		void Waveform::SetHeader(uint8_t asic, uint8_t chan, uint16_t samples, bool errflag) {  // for use in simulation mode
			// TODO(Harm) - consistency check of pack and unpack with simulator
			fData[0] = static_cast<uint8_t>(((chan << 1) & 0x1E) | ((asic << 5) & 0x60) | 0x80);
			if (errflag) { fData[0] |= 0x1; }
			fData[1] = (samples >> 4 & 0x3F);
		}//void Waveform::SetHeader

		void Waveform::PackWaveform(uint8_t asic, uint8_t chan, uint16_t samples, bool errflag, uint16_t* data) {
			SetHeader(asic, chan, samples, errflag);
			for (uint16_t i = 0; i < samples; ++i) {
				uint16_t d = 0;
				// sin waves of changing phase as sample data set, when no data is provided
				if (data != NULL) { d = data[i]; }
				else { d = (uint16_t)(500. +  200. * sin((asic * 16 + chan) / 64. + i * 10. / samples)); }
				SetADC(i, d);
			}
		}//void Waveform::PackWaveform
	}  // namespace TargetDriver
}  // namespace CTA
