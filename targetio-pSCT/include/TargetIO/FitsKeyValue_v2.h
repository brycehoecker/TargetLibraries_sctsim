#ifndef INCLUDE_TARGETIO_FITSKEYVALUE_H_
#define INCLUDE_TARGETIO_FITSKEYVALUE_H_

#include <complex>                        // Include support for complex numbers
#include <cstring>                        // Include C-style string functions
#include <memory>                         // Include smart pointer facilities
#include <string>                         // Include standard string class
#include <typeinfo>                       // Include support for type identification

namespace CTA {                          // Start namespace CTA
	namespace TargetIO {                  // Start nested namespace TargetIO

		class FitsPlaceHolder {           // Begin class definition for FitsPlaceHolder
			public:                         // Public members of the class
				FitsPlaceHolder() {}         // Default constructor
				FitsPlaceHolder(const FitsPlaceHolder&) {}  // Copy constructor
				FitsPlaceHolder& operator=(const FitsPlaceHolder& rhs);  // Copy assignment operator
				virtual ~FitsPlaceHolder() {}  // Virtual destructor

				// Pure virtual functions for derived classes to implement
				virtual bool AsBool() const = 0;                 // Convert to bool
				virtual std::complex<double> AsComplexDouble() const = 0; // Convert to complex double
				virtual double AsDouble() const = 0;            // Convert to double
				virtual std::string AsFitsString() const = 0;   // Convert to FITS format string
				virtual int32_t AsInt() const = 0;              // Convert to int32_t
				virtual int64_t AsInt64() const = 0;            // Convert to int64_t
				virtual std::string AsString() const = 0;       // Convert to string
				virtual bool IsBool() const = 0;                // Check if type is bool
				virtual bool IsComplexDouble() const = 0;       // Check if type is complex double
				virtual bool IsDouble() const = 0;              // Check if type is double
				virtual bool IsInt() const = 0;                 // Check if type is int
				virtual bool IsInt64() const = 0;               // Check if type is int64
				virtual bool IsString() const = 0;              // Check if type is string
		};

		template <typename T>       // Begin template class FitsHolder
		class FitsHolder : public FitsPlaceHolder {  // FitsHolder inherits from FitsPlaceHolder
			private:                // Private members of the class
				
				T fHeld;            // Variable to hold the actual data Template T

			public:                            // Public members of the class
				explicit FitsHolder(const T& pValue = T()) : fHeld(pValue) {} 		// Constructor
				virtual ~FitsHolder() {}        // Virtual destructor

				// Overridden functions from FitsPlaceHolder class
				bool AsBool() const;
				std::complex<double> AsComplexDouble() const;
				double AsDouble() const;
				std::string AsFitsString() const;
				int32_t AsInt() const;
				int64_t AsInt64() const;
				std::string AsString() const;
				bool IsBool() const { return typeid(T) == typeid(bool); }  							// Check if type is bool
				bool IsComplexDouble() const { return typeid(T) == typeid(std::complex<double>); } 	// Check if type is complex double
				bool IsDouble() const { return typeid(T) == typeid(double); } 						// Check if type is double
				bool IsInt() const { return typeid(T) == typeid(int32_t); }   						// Check if type is int
				bool IsInt64() const { return typeid(T) == typeid(int64_t); } 						// Check if type is int64
				bool IsString() const { return typeid(T) == typeid(std::string); } 					// Check if type is string
		};

		class FitsKeyValue {                // Begin class definition for FitsKeyValue
			private:                         // Private members of the class
				std::unique_ptr<FitsPlaceHolder> fContent;  // Smart pointer to FitsPlaceHolder

			public:                          // Public members of the class
				FitsKeyValue();              // Default constructor
				FitsKeyValue(const FitsKeyValue& pValue);  // Copy constructor
				template <typename T>
				explicit FitsKeyValue(const T& pValue);    // Constructor with template parameter

				FitsKeyValue& operator=(const FitsKeyValue& rhs);  // Copy assignment operator
				virtual ~FitsKeyValue() {}   // Virtual destructor

				// Functions to provide access to FitsPlaceHolder functionality
				bool AsBool() const { return fContent ? fContent->AsBool() : 0; } 		// Returns boolean value of fContent, 0 if null
				std::complex<double> AsComplexDouble() const {
					return fContent ? fContent->AsComplexDouble() : 0; 					// Returns complex double value of fContent, 0 if null
				}
				double AsDouble() const { return fContent ? fContent->AsDouble() : 0; } // Returns double value of fContent, 0 if null
				std::string AsFitsString() const {
					return fContent ? fContent->AsFitsString() : ""; 					// Returns FITS string representation of fContent, empty if null
				}
				int32_t AsInt() const { return fContent ? fContent->AsInt() : 0; } 				// Returns int32_t value of fContent, 0 if null
				int64_t AsInt64() const { return fContent ? fContent->AsInt64() : 0; } 			// Returns int64_t value of fContent, 0 if null
				std::string AsString() const { return fContent ? fContent->AsString() : ""; } 	// Returns string value of fContent, empty if null
				bool IsBool() const { return fContent ? fContent->IsBool() : false; } 			// Checks if fContent is of bool type, returns false if null
				bool IsComplexDouble() const {
					return fContent ? fContent->IsComplexDouble() : false; 					// Checks if fContent is of complex double type, returns false if null
				}
				bool IsDouble() const { return fContent ? fContent->IsDouble() : false; } 	// Checks if fContent is of double type, returns false if null
				bool IsInt() const { return fContent ? fContent->IsInt() : false; } 		// Checks if fContent is of int32_t type, returns false if null
				bool IsInt64() const { return fContent ? fContent->IsInt64() : false; } 	// Checks if fContent is of int64_t type, returns false if null
				bool IsString() const { return fContent ? fContent->IsString() : false; } 	// Checks if fContent is of string type, returns false if null

				// Conversion operators to various types
				operator bool() { return AsBool(); } 								// Conversion operator to bool
				operator std::complex<double>() { return AsComplexDouble(); } 		// Conversion operator to std::complex<double>
				operator double() { return AsDouble(); } 							// Conversion operator to double
				operator int32_t() { return AsInt(); } 								// Conversion operator to int32_t
				operator int64_t() { return AsInt64(); } 							// Conversion operator to int64_t
				operator std::string() { return AsString(); } 						// Conversion operator to std::string
		};

	}  // End of namespace TargetIO
}  // End of namespace CTA
#endif  // INCLUDE_TARGETIO_FITSKEYVALUE_H_
