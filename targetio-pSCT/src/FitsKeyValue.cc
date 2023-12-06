// Copyright (c) 2015 The CTA Consortium. All rights reserved.
extern "C" {
#include <fitsio2.h>
}

// Need these two lines to use int32_t and int64_t in format
#ifndef __STDC_FORMAT_MACROS
#define __STDC_FORMAT_MACROS
#endif
#include <inttypes.h>
#include <memory>
#include <string>
#include "TargetIO/FitsKeyValue.h"

namespace CTA {
	namespace TargetIO {

		FitsPlaceHolder& FitsPlaceHolder::operator=(const FitsPlaceHolder& rhs) {
			if (this != &rhs) {
				// do nothing
			}
			return *this;
		}

		template <typename T>
		bool FitsHolder<T>::AsBool() const {
			return static_cast<bool>(fHeld);
		}

		template <>
		bool FitsHolder<std::complex<double>>::AsBool() const {
			return ((fHeld.real() == 0 && fHeld.imag() == 0) ? false : true);
		}

		template <>
		bool FitsHolder<std::string>::AsBool() const {
			if (fHeld == "0" || fHeld == "f" || fHeld == "F") {
				return false;
			}
			return true;
		}

		template <>
		double FitsHolder<std::string>::AsDouble() const {
			return static_cast<double>(std::atof(fHeld.c_str()));
		}

		template <typename T>
		std::complex<double> FitsHolder<T>::AsComplexDouble() const {
			// TODO(Akira): Cannot remove -Wconversion warning in GCC even if static_cast
			// is used here.
			return std::complex<double>(fHeld);
		}

		template <>
		std::complex<double> FitsHolder<std::string>::AsComplexDouble() const {
			return std::complex<double>(std::atof(fHeld.c_str()), 0.);
		}

		template <typename T>
		double FitsHolder<T>::AsDouble() const {
			return static_cast<double>(fHeld);
		}

		template <>
		double FitsHolder<std::complex<double>>::AsDouble() const {
			return fHeld.real();
		}

		template <typename T>
		std::string FitsHolder<T>::AsFitsString() const {
			char str[21];
			snprintf(str, sizeof(str), "%20s", AsString().c_str());
			return std::string(str);
		}

		template <>
		std::string FitsHolder<std::string>::AsFitsString() const {
			std::string ret = "";
			std::string org = AsString();

			for (uint32_t i = 0; i < org.length(); ++i) {
			if (org[i] == '\'') {
			ret += "''";
			} else {
			ret += org[i];
			}
			}

			ret = "'" + ret + "'";
			return ret;
		}

		template <typename T>
			int32_t FitsHolder<T>::AsInt() const {
			return int32_t(fHeld);
		}

		template <>
			int32_t FitsHolder<std::complex<double>>::AsInt() const {
			return int32_t(fHeld.real());
		}

		template <>
			int32_t FitsHolder<std::string>::AsInt() const {
			return int32_t(std::atoi(fHeld.c_str()));
		}

		template <typename T>
			int64_t FitsHolder<T>::AsInt64() const {
			return int64_t(fHeld);
		}

		template <>
			int64_t FitsHolder<std::complex<double>>::AsInt64() const {
			return int64_t(fHeld.real());
		}

		template <>
			int64_t FitsHolder<std::string>::AsInt64() const {
			return int64_t(std::atoi(fHeld.c_str()));
		}

		template <typename T>
			std::string FitsHolder<T>::AsString() const {
			return std::string(fHeld);
		}

		template <>
			std::string FitsHolder<bool>::AsString() const {
			return fHeld == true ? "T" : "F";
		}

		template <>
		std::string FitsHolder<std::complex<double>>::AsString() const {
			char val[FLEN_VALUE], real[FLEN_VALUE], imag[FLEN_VALUE];

			int status = 0;
			ffd2e(fHeld.real(), -15, real, &status);
			ffd2e(fHeld.imag(), -15, imag, &status);
			snprintf(val, FLEN_VALUE, "(%s,%s)", real, imag);

			return std::string(val);
		}

		template <>
		std::string FitsHolder<double>::AsString() const {
			char valstring[FLEN_VALUE];

			int status = 0;
			ffd2e(fHeld, -15, valstring, &status);

			return std::string(valstring);
		}

		template <>
			std::string FitsHolder<int32_t>::AsString() const {
			char str[100];
			snprintf(str, sizeof(str), "%" PRId64, int64_t(fHeld));
			return std::string(str);
		}

		template <>
		std::string FitsHolder<int64_t>::AsString() const {
			char str[100];
			snprintf(str, sizeof(str), "%" PRId64, int64_t(fHeld));
			return std::string(str);
		}

		FitsKeyValue::FitsKeyValue() {
			fContent = std::unique_ptr<FitsPlaceHolder>();
		}

		template <typename T>
		FitsKeyValue::FitsKeyValue(const T&) {
			// Template constructor which prohibits unexpected types. You can use only
			// - bool
			// - double
			// - int32_t
			// - int64_t
			// - std::complex<double>
			// These type have own specialized constructors. So other type must be
			// converted to null string here.
			fContent = std::unique_ptr<FitsPlaceHolder>(new FitsHolder<std::string>(""));
		}

		template <>
		FitsKeyValue::FitsKeyValue(const bool& pValue) {
			// Specialized constructor for bool
			fContent = std::unique_ptr<FitsPlaceHolder>(new FitsHolder<bool>(pValue));
		}

		template <>
		FitsKeyValue::FitsKeyValue(const double& pValue) {
			// Specialized constructor for double
			fContent = std::unique_ptr<FitsPlaceHolder>(new FitsHolder<double>(pValue));
		}

		template <>
		FitsKeyValue::FitsKeyValue(const int32_t& pValue) {
			// Specialized constructor for int32_t
			fContent = std::unique_ptr<FitsPlaceHolder>(new FitsHolder<int32_t>(pValue));
		}

		template <>
		FitsKeyValue::FitsKeyValue(const int64_t& pValue) {
			// Specialized constructor for int64_t
			fContent = std::unique_ptr<FitsPlaceHolder>(new FitsHolder<int64_t>(pValue));
		}

		template <>
		FitsKeyValue::FitsKeyValue(const std::complex<double>& pValue) {
			// Specialized constructor for std::complex<double>
			fContent = std::unique_ptr<FitsPlaceHolder>(
			new FitsHolder<std::complex<double>>(pValue));
		}

		template <>
		FitsKeyValue::FitsKeyValue(const std::string& pValue) {
			// Specialized constructor for std::string
			fContent = std::unique_ptr<FitsPlaceHolder>(new FitsHolder<std::string>(pValue));
		}

		FitsKeyValue::FitsKeyValue(const FitsKeyValue& pValue) {
			if (pValue.fContent) {
				if (pValue.IsBool()) {
					fContent = std::unique_ptr<FitsPlaceHolder>(
					new FitsHolder<bool>(pValue.AsBool()));
				} else if (pValue.IsComplexDouble()) {
					fContent = std::unique_ptr<FitsPlaceHolder>(
					new FitsHolder<std::complex<double>>(pValue.AsComplexDouble()));
				} else if (pValue.IsDouble()) {
					fContent = std::unique_ptr<FitsPlaceHolder>(
					new FitsHolder<double>(pValue.AsDouble()));
				} else if (pValue.IsInt()) {
					fContent = std::unique_ptr<FitsPlaceHolder>(
					new FitsHolder<int32_t>(pValue.AsInt()));
				} else if (pValue.IsInt64()) {
					fContent = std::unique_ptr<FitsPlaceHolder>(
					new FitsHolder<int64_t>(pValue.AsInt64()));
				} else if (pValue.IsString()) {
					fContent = std::unique_ptr<FitsPlaceHolder>(
					new FitsHolder<std::string>(pValue.AsString()));
				}
			} else {
				fContent = std::unique_ptr<FitsPlaceHolder>();
			}
		}

		FitsKeyValue& FitsKeyValue::operator=(const FitsKeyValue& rhs) {
		if (this != &rhs) {
			if (rhs.fContent) {
				if (rhs.IsBool()) {
					fContent = std::unique_ptr<FitsPlaceHolder>(
					new FitsHolder<bool>(rhs.AsBool()));
				} else if (rhs.IsComplexDouble()) {
					fContent = std::unique_ptr<FitsPlaceHolder>(
					new FitsHolder<std::complex<double>>(rhs.AsComplexDouble()));
				} else if (rhs.IsDouble()) {
					fContent = std::unique_ptr<FitsPlaceHolder>(
					new FitsHolder<double>(rhs.AsDouble()));
				} else if (rhs.IsInt()) {
					fContent = std::unique_ptr<FitsPlaceHolder>(
					new FitsHolder<int32_t>(rhs.AsInt()));
				} else if (rhs.IsInt64()) {
					fContent = std::unique_ptr<FitsPlaceHolder>(
					new FitsHolder<int64_t>(rhs.AsInt64()));
				} else if (rhs.IsString()) {
					fContent = std::unique_ptr<FitsPlaceHolder>(
					new FitsHolder<std::string>(rhs.AsString()));
				}
			} else {
				fContent = std::unique_ptr<FitsPlaceHolder>();
			}
		}

		return *this;
		}
	}  // namespace TargetIO
}  // namespace CTA
