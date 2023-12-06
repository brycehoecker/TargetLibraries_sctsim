// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include <fitsio.h>
#include <iostream>
#include "TargetIO/FitsCardImage.h"
#include "TargetIO/FitsKeyValue.h"

namespace CTA {
	namespace TargetIO {

		FitsCardImage::~FitsCardImage() {}

		FitsCardImage::FitsCardImage(const std::string& pKeyword, const std::string& pComment)
			: fComment(pComment), fKeyword(pKeyword), fValue(std::make_shared<FitsKeyValue>()) {
		// constructor for null keyword value (e.g. COMMENT, HISTORY)
		}

		FitsCardImage::FitsCardImage(const std::string& pKeyword,
						 const FitsKeyValue& pValue,
						 const std::string& pComment)
		: fComment(pComment), fKeyword(pKeyword) {
		fValue = std::make_shared<FitsKeyValue>(pValue);
		}

		FitsCardImage::FitsCardImage(const std::string& pKeyword, bool pValue,
						 const std::string& pComment)
		: fComment(pComment), fKeyword(pKeyword) {
		fValue = std::make_shared<FitsKeyValue>(pValue);
		}

		FitsCardImage::FitsCardImage(const std::string& pKeyword, double pValue,
						 const std::string& pComment)
		: fComment(pComment), fKeyword(pKeyword) {
		fValue = std::make_shared<FitsKeyValue>(pValue);
		}

		FitsCardImage::FitsCardImage(const std::string& pKeyword, float pValue,
						 const std::string& pComment)
		: fComment(pComment), fKeyword(pKeyword) {
		fValue = std::make_shared<FitsKeyValue>(static_cast<double>(pValue));
		}

		FitsCardImage::FitsCardImage(const std::string& pKeyword, int32_t pValue,
						 const std::string& pComment)
		: fComment(pComment), fKeyword(pKeyword) {
		fValue = std::make_shared<FitsKeyValue>(pValue);
		}

		FitsCardImage::FitsCardImage(const std::string& pKeyword, int64_t pValue,
						 const std::string& pComment)
		: fComment(pComment), fKeyword(pKeyword) {
		fValue = std::make_shared<FitsKeyValue>(pValue);
		}

		FitsCardImage::FitsCardImage(const std::string& pKeyword,
						 const std::complex<double>& pValue,
						 const std::string& pComment)
		: fComment(pComment), fKeyword(pKeyword) {
		fValue = std::make_shared<FitsKeyValue>(pValue);
		}

		FitsCardImage::FitsCardImage(const std::string& pKeyword,
						 const std::complex<float>& pValue,
						 const std::string& pComment)
		: fComment(pComment), fKeyword(pKeyword) {
		fValue = std::make_shared<FitsKeyValue>(std::complex<double>(pValue));
		}

		FitsCardImage::FitsCardImage(const std::string& pKeyword, const char* pValue,
						 const std::string& pComment)
		: fComment(pComment), fKeyword(pKeyword) {
		fValue = std::make_shared<FitsKeyValue>(std::string(pValue));
		}

		FitsCardImage::FitsCardImage(const std::string& pKeyword,
						 const std::string& pValue,
						 const std::string& pComment)
		: fComment(pComment), fKeyword(pKeyword) {
		fValue = std::make_shared<FitsKeyValue>(pValue);
		}

		bool FitsCardImage::IsCommentary() const {
		if (IsComment() || IsHistory() || GetKeyword().length() == 0) {
		return true;
		}

		return false;
		}

		void FitsCardImage::Print() const { printf("%-80s", ToString().c_str()); }

		void FitsCardImage::SetEmptyValue() {
		fValue = std::make_shared<FitsKeyValue>();
		}

		void FitsCardImage::SetValue(const FitsKeyValue& pValue) {
		fValue = std::make_shared<FitsKeyValue>(pValue);
		}

		void FitsCardImage::SetValue(bool pValue) {
		fValue = std::make_shared<FitsKeyValue>(pValue);
		}

		void FitsCardImage::SetValue(double pValue) {
		fValue = std::make_shared<FitsKeyValue>(pValue);
		}

		void FitsCardImage::SetValue(int32_t pValue) {
		fValue = std::make_shared<FitsKeyValue>(pValue);
		}

		void FitsCardImage::SetValue(int64_t pValue) {
		fValue = std::make_shared<FitsKeyValue>(pValue);
		}

		void FitsCardImage::SetValue(const std::complex<double>& pValue) {
		fValue = std::make_shared<FitsKeyValue>(pValue);
		}

		void FitsCardImage::SetValue(const std::string& pValue) {
		fValue = std::make_shared<FitsKeyValue>(pValue);
		}

		std::string FitsCardImage::ToString() const {
		// Returns 80-char length string in FITS format
		// If the card is commentary 80 x n length string is returned

		static char c81[80];

		if (IsComment() || IsHistory()) {
		std::string comment = GetComment();
		// Calculate the number of lines
		std::size_t n =
		comment.length() / 72 + (comment.length() % 72 == 0 ? 0 : 1);
		if (n == 0) {
		snprintf(c81, sizeof(c81), "%-80s", GetKeyword().c_str());
		return std::string(c81);
		} else {
		std::string str = "";
		for (std::size_t i = 0; i < n; ++i) {
		char c9[9];
		snprintf(c9, sizeof(c9), "%-8s", GetKeyword().c_str());
		str += std::string(c9);
		char c73[73];
		if (i < n - 1) {
		strncpy(c73, &comment[i * 72], 72);
		c73[72] = '\0';
		str += std::string(c73);
		} else {
		str += std::string(&comment[i * 72]);
		}
		}
		return str;
		}
		} else if (GetKeyword() == "") {
		snprintf(c81, sizeof(c81), "%-80s", "");
		return std::string(c81);
		} else {
		// returns a string like "KEYWORD = VALUE / COMMENT"
		snprintf(c81, sizeof(c81), "%-8s= %-20s / %s", GetKeyword().c_str(),
		 fValue ? fValue->AsFitsString().c_str() : "",
		 GetComment().c_str());
		std::string str(c81);
		str.resize(80);
		snprintf(c81, sizeof(c81), "%-80s", str.c_str());
		return std::string(c81);
		}

		snprintf(c81, sizeof(c81), "%-80s", "");
		return std::string(c81);
		}

	}  // namespace TargetIO
}  // namespace CTA
