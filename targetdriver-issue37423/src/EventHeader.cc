// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include "TargetDriver/EventHeader.h"

namespace CTA {
	namespace TargetDriver {
		const std::vector<std::string> EventHeader::kColumnType = {"EVENT_ID", "TACK_32MSB", "TACK_32LSB", "N_PACKETS_FILLED", "TIME_STAMP_SEC", "TIME_STAMP_NSEC"};  // NOLINT(whitespace/line_length)
		const std::vector<std::string> EventHeader::kColumnForm = {"1V",       "1V",         "1V",         "1U",               "1K",             "1K"};               // NOLINT(whitespace/line_length)
		const std::vector<std::string> EventHeader::kColumnUnit = {"",         "",           "",           "",                 "s",              "ns"};               // NOLINT(whitespace/line_length)
	}// namespace TargetDriver
}// namespace CTA
