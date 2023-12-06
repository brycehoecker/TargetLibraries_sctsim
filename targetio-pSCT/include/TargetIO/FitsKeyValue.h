// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#ifndef INCLUDE_TARGETIO_FITSKEYVALUE_H_
#define INCLUDE_TARGETIO_FITSKEYVALUE_H_

#include <complex>
#include <cstring>
#include <memory>
#include <string>
#include <typeinfo>

namespace CTA {
	namespace TargetIO {
		class FitsPlaceHolder {
			public:
				FitsPlaceHolder() {}
				FitsPlaceHolder(const FitsPlaceHolder&) {}
				FitsPlaceHolder& operator=(const FitsPlaceHolder& rhs);
				virtual ~FitsPlaceHolder() {}
				
				virtual bool AsBool() const = 0;
				virtual std::complex<double> AsComplexDouble() const = 0;
				virtual double AsDouble() const = 0;
				virtual std::string AsFitsString() const = 0;
				virtual int32_t AsInt() const = 0;
				virtual int64_t AsInt64() const = 0;
				virtual std::string AsString() const = 0;
				virtual bool IsBool() const = 0;
				virtual bool IsComplexDouble() const = 0;
				virtual bool IsDouble() const = 0;
				virtual bool IsInt() const = 0;
				virtual bool IsInt64() const = 0;
				virtual bool IsString() const = 0;
		};

		template <typename T>
		class FitsHolder : public FitsPlaceHolder {
			private:
				T fHeld;  // Actual data holder

			public:
				explicit FitsHolder(const T& pValue = T()) : fHeld(pValue) {}
				virtual ~FitsHolder() {}

				bool AsBool() const;
				std::complex<double> AsComplexDouble() const;
				double AsDouble() const;
				std::string AsFitsString() const;
				int32_t AsInt() const;
				int64_t AsInt64() const;
				std::string AsString() const;
				bool IsBool() const {
					return typeid(T) == typeid(bool);  // NOLINT(readability/function)
				}
				bool IsComplexDouble() const {
					return typeid(T) == typeid(std::complex<double>);  // NOLINT(readability/function)
				}
				bool IsDouble() const {
					return typeid(T) == typeid(double);  // NOLINT(readability/function)
				}
				bool IsInt() const { return typeid(T) == typeid(int32_t); }
				bool IsInt64() const { return typeid(T) == typeid(int64_t); }
				bool IsString() const { return typeid(T) == typeid(std::string); }
		};

		class FitsKeyValue {
			private:
				std::unique_ptr<FitsPlaceHolder> fContent;  // Pointer to the data

			public:
				FitsKeyValue();
				FitsKeyValue(const FitsKeyValue& pValue);
				template <typename T>
				explicit FitsKeyValue(const T& pValue);
				
				FitsKeyValue& operator=(const FitsKeyValue& rhs);
				virtual ~FitsKeyValue() {}

				bool AsBool() const { return fContent ? fContent->AsBool() : 0; }
				std::complex<double> AsComplexDouble() const {
					return fContent ? fContent->AsComplexDouble() : 0;
				}
				double AsDouble() const { return fContent ? fContent->AsDouble() : 0; }
				std::string AsFitsString() const {
					return fContent ? fContent->AsFitsString() : "";
				}
				int32_t AsInt() const { return fContent ? fContent->AsInt() : 0; }
				int64_t AsInt64() const { return fContent ? fContent->AsInt64() : 0; }
				std::string AsString() const { return fContent ? fContent->AsString() : ""; }
				bool IsBool() const { return fContent ? fContent->IsBool() : false; }
				bool IsComplexDouble() const {
					return fContent ? fContent->IsComplexDouble() : false;
				}
				bool IsDouble() const { return fContent ? fContent->IsDouble() : false; }
				bool IsInt() const { return fContent ? fContent->IsInt() : false; }
				bool IsInt64() const { return fContent ? fContent->IsInt64() : false; }
				bool IsString() const { return fContent ? fContent->IsString() : false; }

				operator bool() { return AsBool(); }
				operator std::complex<double>() { return AsComplexDouble(); }
				operator double() { return AsDouble(); }
				operator int32_t() { return AsInt(); }
				operator int64_t() { return AsInt64(); }
				operator std::string() { return AsString(); }
		};
	}  // namespace TargetIO
}  // namespace CTA

#endif  // INCLUDE_TARGETIO_FITSKEYVALUE_H_
